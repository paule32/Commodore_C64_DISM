"""Stage 409: end-to-end D64 bytes and both VICE launch paths (without VICE GUI)."""
import tempfile
import unittest
from pathlib import Path

from c64_d64_disk import (
    DISK_SIZE, TRACK_SECTORS, _offset, build_1541_d64,
    c64_vice_d64_command_options, c64_vice_d64_autostart_options, prepare_c64_sprite_disk,
)
from c64_vice_assets import c64_vice_sprite_program

ROOT = Path(__file__).parent


def entries_and_content(image):
    """Independent sector-chain validator and directory walker."""
    assert len(image) == 174848
    t, s = 18, 1
    found = {}
    visited = set()
    while t:
        assert (t, s) not in visited
        visited.add((t, s))
        o = _offset(t, s)
        next_t, next_s = image[o:o+2]
        for slot in range(8):
            d = o + slot * 32
            typ = image[d+2]
            if not typ:
                continue
            assert typ == 0x82, (t, s, slot, typ)
            name = image[d+5:d+21].rstrip(b'\xa0').decode('ascii')
            start = tuple(image[d+3:d+5]); chain = []
            payload = bytearray()
            while start[0]:
                assert start not in chain
                chain.append(start)
                x = _offset(*start)
                nt, ns = image[x:x+2]
                if nt:
                    payload.extend(image[x+2:x+256])
                    start = (nt, ns)
                else:
                    assert 1 <= ns <= 255
                    payload.extend(image[x+2:x+2+ns-1])
                    start = (0, 0)
            assert int.from_bytes(image[d+30:d+32], 'little') == len(chain)
            found[name] = bytes(payload)
        t, s = next_t, next_s
    return found


class Stage409D64Tests(unittest.TestCase):
    def test_two_prg_files_have_correct_chains_and_bam(self):
        sprite = b'\x00\x30' + bytes(range(128))
        executable = b'\x01\x08' + bytes((i % 256 for i in range(1300)))
        image = build_1541_d64([('SPRITE_A', executable), ('sprites.spr', sprite)])
        self.assertEqual(len(image), DISK_SIZE)
        self.assertEqual(image[_offset(18, 0):_offset(18, 0)+4], b'\x12\x01\x41\x00')
        self.assertEqual(image[_offset(18, 0)+0x90:_offset(18, 0)+0x9B], b'DBASE2MANY\xa0')
        self.assertEqual(entries_and_content(image), {'SPRITE_A': executable, 'SPRITES.SPR': sprite})
        # Cross-check bitmap free counts and directory sectors.
        for track in range(1, 36):
            off = _offset(18, 0)+4+(track-1)*4
            count = image[off]
            bitmap = int.from_bytes(image[off+1:off+4], 'little')
            self.assertEqual(count, (bitmap & ((1 << TRACK_SECTORS[track])-1)).bit_count())
        self.assertEqual(image[_offset(18, 0)+4+(18-1)*4], 17)

    def test_multiple_directory_sectors_and_all_payload_lengths(self):
        variants = [2, 3, 64, 254, 255, 508, 509, 1025, 8000, 1]
        files = [(f'FILE{i:02d}', b'\x01\x08' + bytes([i])*n)
                 for i, n in enumerate(variants)]
        self.assertEqual(entries_and_content(build_1541_d64(files)), dict(files))

    def test_duplicate_bad_name_and_overflow_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'doppelt'):
            build_1541_d64([('a', b'\x00\x30'), ('A', b'\x00\x30')])
        with self.assertRaisesRegex(ValueError, 'Dateiname'):
            build_1541_d64([('bad/name', b'\x00\x30')])
        with self.assertRaisesRegex(ValueError, 'voll'):
            build_1541_d64([('HUGE', b'\x00\x30'+b'X'*200000)])

    def test_immutable_disk_creation_with_real_sprite_header(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            staging = base / '.d64_dism' / 'vice_drive8'
            staging.mkdir(parents=True)
            raw = bytes(range(128))
            prepared = c64_vice_sprite_program(raw)
            (staging / 'sprites.spr').write_bytes(prepared)
            program = base / 'Sprite_A.prg'
            prg = b'\x01\x08' + bytes(range(180))
            program.write_bytes(prg)
            disk, start_name = prepare_c64_sprite_disk(staging, names=('sprites.spr',),
                                                         program_path=program,
                                                         program_name='SPRITE_A')
            self.assertEqual(start_name, 'SPRITE_A')
            self.assertIn('.d64_dism/vice_disks', disk.as_posix())
            self.assertEqual(entries_and_content(disk.read_bytes()), {'SPRITE_A': prg, 'SPRITES.SPR': prepared})
            self.assertEqual(prepare_c64_sprite_disk(staging, names=('sprites.spr',),
                                                      program_path=program,
                                                      program_name='SPRITE_A')[0], disk)
            self.assertEqual((staging / 'sprites.spr').read_bytes(), prepared)
            self.assertEqual(program.read_bytes(), prg)
            self.assertEqual(c64_vice_d64_command_options(disk), ['-8', str(disk)])
            disk.write_bytes(bytes(DISK_SIZE))
            with self.assertRaises(FileExistsError):
                prepare_c64_sprite_disk(staging, names=('sprites.spr',),
                                        program_path=program, program_name='SPRITE_A')

    def test_basic_direct_disk_has_only_sprites(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'sprites.spr').write_bytes(b'\x00\x30'+bytes(64))
            disk, name = prepare_c64_sprite_disk(folder, names=('sprites.spr',))
            self.assertIsNone(name)
            self.assertEqual(entries_and_content(disk.read_bytes()),
                             {'SPRITES.SPR': b'\x00\x30'+bytes(64)})

    def test_d64_is_used_in_both_vice_launches_without_virtual_fs_override(self):
        text = (ROOT / 'd64_dism.py').read_text(encoding='utf-8')
        main = text[text.index('        def _stage_c64_sprite_disk('):]
        self.assertIn('sprite_disk, disk_program_name = self._stage_c64_sprite_disk(', main)
        self.assertIn('c64_vice_d64_autostart_options(sprite_disk)', main)
        self.assertNotIn("'-autostart', str(sprite_disk) + ':' + disk_program_name", main)
        self.assertIn('command.extend(c64_vice_d64_command_options(sprite_disk))', main)
        self.assertIn('Never call configure_virtual_drive8()', main)
        self.assertNotIn('client.configure_virtual_drive8(sprite_drive)', main)

if __name__ == '__main__':
    unittest.main()
