import os,sys
sys.path.insert(0,os.path.abspath('../src'))

from simulation_class import *
import numpy as np
import unittest
import pickle
from math import *
import sys

script_path = os.path.abspath(".")

class TestSimulationInitializations(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        self.current_folder = os.path.abspath(".")
        self.data_folder =  os.path.abspath("./test_files/simulation_tests/lt_files/nanoparticle_1ddt_1meoh/")
        self.init_file = self.data_folder+"/system.in"
        self.data_file = self.data_folder+"/system.data"
        self.dumpfile =  self.data_folder+"/regrow.xyz"
        self.silver_expected_coords = np.loadtxt(self.current_folder+"/test_files/simulation_tests/expected_silver.xyz",skiprows=2)
        self.adsorbate_expected_coords =  np.loadtxt(self.current_folder+"/test_files/simulation_tests/expected_adsorbate.xyz",skiprows=2)
        self.temp = 298.15
        self.sim = Simulation(self.init_file,self.data_file,self.dumpfile,self.temp)

    def test_initialize_group_by_comparing_silver_xyz_file_with_expected_file(self):
        self.sim.dump_group("silver","silverdump.xyz") 
        actual_coords = np.loadtxt(self.data_folder+"/silverdump.xyz",skiprows=2)
        np.testing.assert_almost_equal(actual_coords,self.silver_expected_coords,decimal=4,err_msg="Coords do not match")
    
    def test_initialize_group_by_comparing_adsorbate_xyz_file_with_expected_file(self):
        self.sim.dump_group("adsorbate","adsorbate.xyz") 
        actual_coords = np.loadtxt(self.data_folder+"/adsorbate.xyz",skiprows=2)
        np.testing.assert_almost_equal(actual_coords,self.adsorbate_expected_coords,decimal=4,err_msg="Coords do not match")

    @classmethod
    def tearDownClass(self):
        os.chdir(script_path)

class TestSimulationPotentialEvaluationsIntramolecular(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.current_folder = script_path
        self.data_folder =  os.path.abspath(script_path+"/test_files/simulation_tests/lt_files/meoh/")
        self.init_file = self.data_folder+"/system.in"
        self.data_file = self.data_folder+"/system.data"
        self.dumpfile =  self.data_folder+"/regrow.xyz"
        self.temp = 298.15
        self.sim = Simulation(self.init_file,self.data_file,self.dumpfile,self.temp)

    def test_getCoulPE_with_lone_MeOH(self):
        #import pdb;pdb.set_trace()
        self.assertAlmostEqual(0.0000,self.sim.getCoulPE(),places=4,msg="getCoulPE does not return the expected coulombic energy for a lone MeOH (it should be 0)")

    def test_getVdwlPE_with_lone_MeOH(self):
        self.assertAlmostEqual(-0.14060,self.sim.getVdwlPE(),places=4,msg="getCoulPE does not return the expected Van der Waals energy for a lone MeOH")

    @classmethod
    def tearDownClass(self):
        os.chdir(script_path)


class TestSimulationPotentialEvaluationIntermolecular(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.current_folder = script_path
        self.data_folder =  os.path.abspath(script_path+"/test_files/simulation_tests/lt_files/two_meohs/")
        self.init_file = self.data_folder+"/system.in"
        self.data_file = self.data_folder+"/system.data"
        self.dumpfile =  self.data_folder+"/regrow.xyz"
        self.temp = 298.15
        self.sim = Simulation(self.init_file,self.data_file,self.dumpfile,self.temp)

    def test_getVdwlPE_with_two_MeOHs_separated_by_5A(self):
        self.assertAlmostEqual(-1.6710847,self.sim.getVdwlPE(),places=4,msg="getVdwlPE does not return expected value for Van der Waals energy of two MeOHs seoarated by 5Angstroms")

    def test_getCoulPE_with_two_MeOHs_separated_by_5A(self):
        self.assertAlmostEqual(0.5628225,self.sim.getCoulPE(),places=4,msg="getCoulPE does not return expected value for Coulombic energy of two MeOHs separated by 5A")

class TestSimulationTurningOffAtoms(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.current_folder = script_path
        self.data_folder =  os.path.abspath(script_path+"/test_files/simulation_tests/lt_files/two_meohs/")
        self.init_file = self.data_folder+"/system.in"
        self.data_file = self.data_folder+"/system.data"
        self.dumpfile =  self.data_folder+"/regrow.xyz"
        self.temp = 298.15
        self.sim = Simulation(self.init_file,self.data_file,self.dumpfile,self.temp)
    
    def test_turn_off_one_hydrogen_in_two_MeOHs_separated_by_5A_check_Van_der_Waals_Energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([5])
        self.assertAlmostEqual(-1.6710847,self.sim.getVdwlPE(),places=4,msg="Turning off a hydrogen atom in 2 MeOH system does not result in correct Vdwl Energy")

    def test_turn_off_one_hydrogen_in_two_MeOHs_separated_by_5A_check_coulombic_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([5])
        self.assertAlmostEqual(1.1598538,self.sim.getCoulPE(),places=4,msg="Turning off a hydrogen atom in 2 MeOH system does not result in correct coulombic energy")

    def test_turn_off_one_hydrogen_and_oxygen_in_two_MeOHs_separated_by_5A_check_Van_der_Waals_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([4,5])
        self.assertAlmostEqual(-1.4003423,self.sim.getVdwlPE(),places=4,msg="Turning off oxygen and hydrogen in a 2 MeOH system does not result in a correct Van der waals Energy")

    def test_turn_off_one_hydrogen_and_oxygen_in_two_MeOHs_separated_by_5A_check_coulombic_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([4,5])
        self.assertAlmostEqual(0.0120187,self.sim.getCoulPE(),places=4,msg="Turning off a oxygen and hydrogen in a 2 MeOH system does not result in a correct coulombic energy")

    def test_turn_off_one_hydrogen_one_oxygen_and_one_carbon_in_two_MeOHs_separated_by_5A_check_Van_der_Waals_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([3,4,5])
        self.assertAlmostEqual(-1.0801268,self.sim.getVdwlPE(),places=4,msg="Turning off a carbon, oxygen, and a hydrogen in a 2 MeOH system does not result in a correct Van der Waals Energy")

    def test_turn_off_one_hydrogen_one_oxygen_and_one_carbon_in_two_MeOHs_separated_by_5A_check_coulombic_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([3,4,5])
        self.assertAlmostEqual(0,self.sim.getCoulPE(),places=4,msg="Turning off a carbon, oxygen, and a hydrogen in a 2 MeOH system does not result in correct coulombic Energy")

    def test_turn_off_one_hydrogen_one_oxygen_and_two_carbon_in_two_MeOHs_separated_by_5A_check_Van_der_Waals_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([2,3,4,5])
        self.assertAlmostEqual(-0.7862932,self.sim.getVdwlPE(),places=4,msg="Turning off two carbons, an oxygen, and a hydrogen in a 2 MeOH system does not result in the correct Van der Waals energy")

    def test_turn_off_one_hydrogen_one_oxygen_and_two_carbon_in_two_MeOHs_separated_by_5A_check_coulombic_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([2,3,4,5])
        self.assertAlmostEqual(0,self.sim.getCoulPE(),places=4,msg="Turning off two carbons, an oxygen, and a hydrogen in a 2 MeOH system does not result in the correct coulombic energy")

    def test_turn_off_one_MeOH_molecule_in_two_MeOHs_separated_by_5A_check_Van_der_Waals_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([1,2,3,4,5])
        self.assertAlmostEqual(-0.1406,self.sim.getVdwlPE(),places=4,msg="Turning off one MeOH in a 2 MeOH does not result in the correct Van der Waals energy")

    def test_turn_off_one_MeOH_molecule_in_two_MeOHs_separated_by_5A_check_coulombic_energy(self):
        self.sim.turn_on_all_atoms()
        self.sim.turn_off_atoms([1,2,3,4,5])
        self.assertAlmostEqual(0,self.sim.getCoulPE(),places=4,msg="Turning off one MeOH in a 2 MeOH does not result in the correct coulombic energy")

    @classmethod
    def tearDownClass(self):
        os.chdir(script_path)


class TestUpdatingCoordinates(unittest.TestCase):

    def setUp(self):
        self.longMessage = True
        self.current_folder = script_path
        self.two_meoh_init_coords = pickle.load(open('./test_files/simulation_tests/two_meoh_coords.pickle','rb'))
        self.two_meoh_final_coords =  pickle.load(open('./test_files/simulation_tests/two_meoh_coords_after_displacement.pickle','rb'))
        self.data_folder =  os.path.abspath(script_path+"/test_files/simulation_tests/lt_files/two_meohs/")
        self.init_file = self.data_folder+"/system.in"
        self.data_file = self.data_folder+"/system.data"
        self.dumpfile =  self.data_folder+"/regrow.xyz"
        self.temp = 298.15
        self.sim = Simulation(self.init_file,self.data_file,self.dumpfile,self.temp)

    def test_get_atoms_returns_correct_coordinates(self):
        atomlist = self.sim.get_atoms()
        atom_coords = [atom.position for atom in atomlist]
        np.testing.assert_array_almost_equal(atom_coords,self.two_meoh_init_coords,err_msg = "get_atoms does not return Atom objects with the correct coordinates.")

    def test_get_coords_updates_atomlist_after_displacement_in_simulation(self):
        self.sim.lmp.command("group test id 6:10")
        self.sim.lmp.command("displace_atoms test move 0 5 0")
        self.sim.get_coords()
        atomlist = self.sim.get_atoms()
        atom_coords = [atom.position for atom in atomlist]
        np.testing.assert_array_almost_equal(atom_coords,self.two_meoh_final_coords,err_msg = "After displacement of atoms in simulation using displace_atoms command the coordinates of the atomlist do not match.")

    def test_update_coords_updates_coordinates_of_simulation_with_correct_atomlist_coords(self):
        atomlist = self.sim.atomlist
        atomlist[0].position[2]=atomlist[0].position[2]+2.5
        backup_coords = np.copy([atom.position for atom in self.sim.atomlist])
        self.sim.update_coords()
        self.sim.get_coords()
        new_coords = [atom.position for atom in self.sim.atomlist]
        np.testing.assert_array_almost_equal(backup_coords,new_coords,err_msg="update_coords does not update the coordinates with the positions given by the atomlilst.")


    def tearDown(self):
        os.chdir(script_path)



