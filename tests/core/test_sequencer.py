import unittest
import string

import forge.sequencer as seq
reload(seq)


class TestSequencer(unittest.TestCase):

    def setUp(self):
        self.seq = seq.Sequencer()

    def tearDown(self):
        del self.seq
    
    def test_numeric(self):                
        test_numeric = "00 01 02 03 04 05 06 07 08 09 10 11".split(' ')
        self.assertEquals(self.seq.name_sequence_fill(0,
                                                      12,
                                                      sequence="numeric"),
                          test_numeric)
        
        test_numeric = "06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23".split(' ')
        self.assertEquals(self.seq.name_sequence_fill(6,
                                                      18,
                                                      sequence="numeric"),
                          test_numeric)

    
    def test_alpha(self):
        self.assertEquals(self.seq.name_sequence_fill(0,
                                                      26,
                                                      capital=True,
                                                      sequence="alpha"),
                          list(string.uppercase))
        
        test_alpha = "AA AB AC AD AE AF AG AH AI AJ AK AL AM AN AO AP AQ AR AS AT AU AV AW AX AY AZ BA BB".split(' ')
        self.assertEquals(self.seq.name_sequence_fill(0,
                                                      28,
                                                      capital=True,
                                                      sequence="alpha"),
                          test_alpha)
        
        test_alpha = "AY AZ BA BB BC BD BE BF BG BH BI BJ".split(' ')
        self.assertEquals(self.seq.name_sequence_fill(24,
                                                      12,
                                                      capital=True,
                                                      sequence="alpha"),
                          test_alpha)

    
    def test_hex(self):
        test_hex = "0 1 2 3 4 5 6 7 8 9 A B".split(' ')
        self.assertEquals(self.seq.name_sequence_fill(0,
                                                      12,
                                                      capital=True,
                                                      sequence="hexa"),
                          test_hex)
        
        test_hex = "06 07 08 09 0A 0B 0C 0D 0E 0F 10 11 12 13 14 15 16 17".split(' ')

        self.assertEquals(self.seq.name_sequence_fill(6,
                                                      18,
                                                      pad_override=2,
                                                      capital=True,
                                                      sequence="hexa"),
                          test_hex)

    
    def test_seq(self):
        test_seq = "CatPlane CatTrain CatApple DogCat DogDog DogCar DogPlane".split(' ')
        self.assertEquals(self.seq.name_sequence_fill(3,
                                                      7,
                                                      pad_override=2,
                                                      sequence=["Cat","Dog","Car","Plane","Train","Apple"]),
                          test_seq)

    
    def test_sequence_input(self):
        with self.assertRaises(KeyError):
            self.seq.name_sequence_fill(3, 7, sequence="fail")

if __name__ == '__main__':
    unittest.main()