import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSpellCorrection:
    """Unit tests for spell correction"""

    def test_correct_typo(self):
        """Test basic typo correction"""
        from spell_check import correct_query
        result = correct_query('chiken')
        assert result['has_correction'] == True
        assert result['corrected'] == 'chicken'

    def test_correct_word_unchanged(self):
        """Test correct word not changed"""
        from spell_check import correct_query
        result = correct_query('chicken')
        assert result['has_correction'] == False
        assert result['corrected'] == 'chicken'

    def test_multiple_typos(self):
        """Test multiple typos corrected"""
        from spell_check import correct_query
        result = correct_query('chiken past')
        assert result['has_correction'] == True

    def test_preprocess_query(self):
        """Test query preprocessing"""
        from spell_check import preprocess_query
        result = preprocess_query('chicken pasta cooking')
        assert isinstance(result, str)
        assert len(result) > 0