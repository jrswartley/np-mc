import random as rnd
import numpy as np
import forcefield_class as ffc
import scipy.misc as scm
from math import pi,acos,sin,cos

class Move(object):
    """A class used to encapsulate all MC moves that can be used by a simulation.  

    Parameters
    ----------
    lmp : lammps object
        The lammps instance associated with the simulation.  Passed in so that the move can evaluate energies of moves and thereby calculate probabilities of acceptance.

    molecules : list of type Molecule
        A list of molecules that are available to apply a MC move to.

    temp : float
        The temperature of the simulation in Kelvin.
    """
    def __init__(self,simulation):
        self.simulation =simulation
        self.lmp = simulation.lmp
        self.molecules = simulation.molecules
        self.temp = simulation.temp
        self.kb = 0.0019872041

class CBMCRegrowth(Move):
    """A class that encapsulates a Configurationally Biased Regrowth move as outline by Siepmann et al. that inherits from the Move class.  
    Here the dihedral force fields of the simulation are also passed in to ais in choosing trial positions.

    Parameters
    ----------
    dihedral_ffs : list of type DihedralForceField
        A list of DihedralForceField objects associated with the simulation

    lmp : lammps object
        The lammps instance associated with the simulation.  Passed in so that the move can evaluate energies of moves and thereby calculate probabilities of acceptance.

    molecules : list of type Molecule
        A list of molecules that are available to apply a MC move to.

    numtrials : int
        The number of trial placements used at each step of the regrowth move.  Default is 5 trials.

    anchortype : int
        The type number in the LAMMPS file used for the atom type used for the anchor atom in each molecule.
    """
    def __init__(self,simulation,anchortype,numtrials=5):
        self.dihedral_ffs = ffc.initialize_dihedral_ffs(simulation.init_file+'.settings')
        self.numtrials = numtrials
        super(CBMCRegrowth,self).__init__(simulation)
        self.anchortype = anchortype
        self.set_anchor_atoms()
        self.rosen_file = open('Rosenbluth_Data.txt','a')
        self.rosen_file.write('log_Wo\tlog_Wf\tprobability\tNew Energy\taccepted\n')
        self.lmp_clones = [self.simulation.clone_lammps() for i in range(5)]

    def select_random_molecule(self):
        """Selects a random elegible molecule (one with an anchor atom set) from the molecules provided by the Simulation object that the CBMCRegrowth object was passed in at initialization.

        Returns
        -------
        Random Elegible Molecule : Molecule
            A randomly chosen molecule from the list of elegible ones.
        """
        elegible_molecules = [molecule for key,molecule in self.molecules.items() if (self.anchortype in [atom.atomType for atom in molecule.atoms])]
        return(rnd.choice(elegible_molecules))

    def set_anchor_atoms(self):
        """For every molecule in the Move's associated simulation the anchor atom is set to the anchortype associated with the CBMCRegrowth instance.  
        Any molecule that does not have an atom of type anchortype is skipped.
        """
        for key, molecule in self.simulation.molecules.iteritems():
            anchorIDs = [atom.atomID for atom in molecule.atoms if atom.atomType==self.anchortype]
            if len(anchorIDs)>0:
                molecule.setAnchorAtom(anchorIDs[0])

    def select_index(self,molecule):
        """Selects a random index of a molecule ranging from 3 to the final index.  The index selection starts at 3 as no dihedral rotation does not move any atoms with index less than 3.

        Parameters
        ----------
        molecule : Molecule
            The Molecule objectone wishes to select a ranomd index from.

        Returns
        -------
        index : int
            A random index from 3 to length of molecule.      
        """
        return(rnd.randrange(3,len(molecule.atoms)))

    def select_dih_angles(self,dih_type):
        """Returns numtrials number of dihedral angles with probability given by the PDF given by the boltzmann distribution determined by the temperature and the dihedral forcefield.

        Parameters
        ----------
        dih_type : int
            An integer which corresponds to the type of Dihedral one wishes to samples.

        Returns
        -------
        trial_dih_angles : Numpy array of floats
            An array of floats which correspond to the selected dihedral angles in radians.
        """
        force_field = [ff for ff in self.dihedral_ffs if ff.dihedral_type==dih_type][0]
        (thetas,ff_pdf) = force_field.get_pdf(self.temp)
        dtheta = thetas[1]-thetas[0]
        trial_dih_angles = np.random.choice(thetas,size=self.numtrials,p=ff_pdf*dtheta)
        return(trial_dih_angles)

    def parallel_evaluate_energies(self,molecule,index,rotations):
        coords = [atom.position for atom in self.simulation.atomlist]
        for i,rotations in enumerate(rotations):
            print("placeholder")

    def evaluate_energies(self,molecule,index,rotations):
        """Evluates the pair energy of the system for each of the given dihedral rotations at the specified index.  For these enegies to be consistent with CBMC all atoms past the index should be turned off with turn_off_molecule_atoms.
        
        Parameters
        ----------
        molecule : Molecule
            The molecule on which the dihedral rotations will be carried out
        index : int
            The index of the atom that is in the last position of the dihedral to be rotated.
        rotations : list of floats
            A list of floats which represent the desired rotation from the current dihedral angle in Radians.

        Returns
        -------
        energies : Numpy array of floats
            An array of the pair energy for each of the specified rotations.
        """
        energies = np.empty(self.numtrials)
        for i,rotation in enumerate(rotations):
            molecule.rotateDihedral(index,rotation)
            self.simulation.update_coords()
            energies[i]=self.simulation.get_pair_PE()
            molecule.rotateDihedral(index,-rotation)
        return(energies)

    def turn_off_molecule_atoms(self,molecule,index): 
        if (index+1>=len(molecule.atoms)):
            self.simulation.turn_on_all_atoms()
            return
        indices_to_turn_off = np.arange(index+1,len(molecule.atoms))
        atoms = map(molecule.getAtomByMolIndex,indices_to_turn_off)
        atomIDs = [atom.atomID for atom in atoms]
        self.simulation.turn_off_atoms(atomIDs)

    def evaluate_trial_rotations(self,molecule,index,keep_original=False):
        beta = 1./(self.kb*self.temp)
        dihedral = molecule.index2dihedral(index)
        thetas = self.select_dih_angles(dihedral.dihType)
        theta0 = molecule.getDihedralAngle(dihedral)
        rotations = thetas-theta0
        if keep_original:
            rotations[0]=0
        self.turn_off_molecule_atoms(molecule,index-1)
        self.simulation.update_coords()
        initial_energy = self.simulation.get_pair_PE()
        self.turn_off_molecule_atoms(molecule,index)
        energies = self.evaluate_energies(molecule,index,rotations)
        log_rosen_weight = scm.logsumexp(-beta*(energies-initial_energy))
        log_norm_probs = -beta*(energies-initial_energy)-log_rosen_weight
        selected_rotation = np.random.choice(rotations,p=np.exp(log_norm_probs))
        return(log_rosen_weight,selected_rotation)

    def regrow(self,molecule,index,keep_original=False):
        total_log_rosen_weight = 0
        for index in range(index,len(molecule.atoms)):             
            self.turn_off_molecule_atoms(molecule,index)
            (log_step_weight,selected_rotation) = self.evaluate_trial_rotations(molecule,index,keep_original)
            rotation = 0 if keep_original else selected_rotation
            molecule.rotateDihedral(index,rotation)
            total_log_rosen_weight+=log_step_weight
        return total_log_rosen_weight

    def move(self):
        molecule = self.select_random_molecule()
        index = self.select_index(molecule) 
        log_Wo = self.regrow(molecule,index,keep_original=True)
        log_Wf = self.regrow(molecule,index)
        probability = min(1,np.exp(log_Wf-log_Wo))
        accepted = probability>rnd.random()
        self.simulation.update_coords()
        self.rosen_file.write(str(log_Wo)+'\t'+str(log_Wf)+'\t'+str(probability)+'\t'+str(self.simulation.get_total_PE())+'\t'+str(accepted)+'\n')
        self.rosen_file.flush()
        return(accepted)

    
class TranslationMove(Move):
    def __init__(self,simulation,max_disp):
        super(TranslationMove,self).__init__(simulation)
        self.max_disp = max_disp

    def translate(self,molecule,move):
        #positions = [atom.position for atom in molecule.atoms]
        #positions = positions+move
        molecule.move_atoms(move)
        self.simulation.update_coords()

    def select_random_molecule(self):
        """Selects a random elegible molecule (one with an anchor atom set) from the molecules provided by the Simulation object that the CBMCRegrowth object was passed in at initialization.

        Returns
        -------
        Random Elegible Molecule : Molecule
            A randomly chosen molecule from the list of elegible ones.
        """
        elegible_molecules = [molecule for key,molecule in self.molecules.items() if (self.anchortype in [atom.atomType for atom in molecule.atoms])]
        return(rnd.choice(elegible_molecules))

    def get_random_move(self):
        theta = 2*pi*rnd.random()
        phi = acos(2*rnd.random()-1)
        r = self.max_disp*rnd.random()
        return(np.array([r*sin(phi)*cos(theta),r*sin(phi)*cos(theta),r*cos(phi)]))

    def move(self):
        beta = 1./(self.kb*self.temp)
        old_energy = self.simulation.get_total_PE()
        molecule = self.select_random_molecule()
        self.translate(molecule,move)
        move = self.get_random_move()
        self.translate(molecule,move)
        new_energy = self.simulation.get_total_PE()
        probability = np.exp(-beta*(new_energy-old_energy))
        return(probability>rnd.random())















