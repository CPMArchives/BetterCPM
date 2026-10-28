"""Ensure the public --build path prepares companion binaries before packaging."""
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
import build_utilities_disk as disk

class BuildSequence(unittest.TestCase):
    def test_companion_builds_precede_packaging(self):
        called=[]
        def run(command,**kwargs):
            called.append(Path(command[1]).stem)
            self.assertTrue(kwargs['check'])
        def package(*args):
            self.assertIn('build_patch',called)
            self.assertIn('build_compare',called)
            self.assertIn('build_noah',called)
        with patch.object(sys,'argv',['build_utilities_disk.py','--build']),patch.object(disk.subprocess,'run',side_effect=run),patch.object(disk,'build',side_effect=package) as build:
            disk.main()
        build.assert_called_once()
    def test_failed_builder_stops_packaging(self):
        import subprocess
        with patch.object(sys,'argv',['build_utilities_disk.py','--build']),patch.object(disk.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'builder')),patch.object(disk,'build') as build:
            with self.assertRaises(subprocess.CalledProcessError):disk.main()
        build.assert_not_called()

if __name__=='__main__':unittest.main()
