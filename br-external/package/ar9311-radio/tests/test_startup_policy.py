#!/usr/bin/env python3
"""Exercise radio startup scheduling with isolated firmware/sysfs/module stubs."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'src/S44ar9311-radio'


class StartupPolicy(unittest.TestCase):
    def run_start(self, defaults='', online=True, cpu_list=None, hotplug=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'defaults').write_text(defaults)
            firmware = root / 'firmware'
            firmware.mkdir()
            for name in ('open8030.img', 'open8030.json'):
                (firmware / name).write_text('fixture')
            cpu = root / 'cpu/cpu1'
            cpu.mkdir(parents=True)
            if hotplug:
                (cpu / 'online').write_text('1' if online else '0')
            (root / 'cpu/online').write_text(cpu_list if cpu_list is not None else ('0-1' if online else '0'))
            calls = root / 'calls'
            stub = root / 'modprobe'
            stub.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$CALLS"\n')
            stub.chmod(0o755)
            text = SCRIPT.read_text()
            for old, new in (
                ('/etc/default/ar9311-radio', str(root / 'defaults')),
                ('/sys/module/arlink', str(root / 'not-loaded')),
                ('/lib/firmware', str(firmware)),
                ('/sys/devices/system/cpu', str(root / 'cpu')),
                ('/dev/arlink0', '/dev/null'),
            ):
                text = text.replace(old, new)
            script = root / 'start'
            script.write_text(text)
            proc = subprocess.run(['sh', str(script), 'start'], text=True,
                                  capture_output=True,
                                  env={**os.environ, 'PATH': f'{root}:/usr/bin:/bin',
                                       'CALLS': str(calls)})
            lines = calls.read_text().splitlines() if calls.exists() else []
            return proc, [line for line in lines if line.startswith('arlink ')]

    def test_default_unchanged(self):
        proc, calls = self.run_start()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(calls, ['arlink fw_name=open8030.img cfg_name=open8030.json'])

    def test_selected_policy(self):
        proc, calls = self.run_start('sdio_rx_cpu=1\nsdio_rx_priority=30\n')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(calls, ['arlink fw_name=open8030.img cfg_name=open8030.json '
                                 'sdio_rx_cpu=1 sdio_rx_priority=30'])

    def test_offline_cpu_does_not_apply_priority_alone(self):
        proc, calls = self.run_start('sdio_rx_cpu=1\nsdio_rx_priority=30\n', online=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn('sdio_rx_', calls[0])
        self.assertIn('CPU unavailable', proc.stderr)

    def test_online_cpu_without_hotplug_files(self):
        proc, calls = self.run_start('sdio_rx_cpu=1\nsdio_rx_priority=30\n', hotplug=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn('sdio_rx_cpu=1 sdio_rx_priority=30', calls[0])

    def test_sparse_online_cpu_ranges(self):
        for cpu, selected in ((0, True), (1, False), (2, True), (3, True), (4, False), (7, True)):
            with self.subTest(cpu=cpu):
                proc, calls = self.run_start(f'sdio_rx_cpu={cpu}\nsdio_rx_priority=30\n',
                                             cpu_list='0,2-3,7', hotplug=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual('sdio_rx_priority=30' in calls[0], selected)

    def test_invalid_policy_never_loads_radio(self):
        for settings in ('sdio_rx_cpu=1', 'sdio_rx_priority=30',
                         'sdio_rx_cpu=-1\nsdio_rx_priority=30',
                         'sdio_rx_cpu=1\nsdio_rx_priority=100',
                         'sdio_rx_cpu=1\nsdio_rx_priority=0'):
            with self.subTest(settings=settings):
                proc, calls = self.run_start(settings)
                self.assertNotEqual(proc.returncode, 0)
                self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
