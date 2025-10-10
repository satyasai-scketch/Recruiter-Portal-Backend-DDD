from difflib import SequenceMatcher
from typing import Dict, Tuple


class JDInlineDiffGenerator:
    """Generate inline diff markup for original and refined JD texts separately"""
    
    @staticmethod
    def generate_marked_texts(original: str, refined: str) -> Tuple[str, str, Dict[str, int]]:
        """
        Generate inline markup for both original and refined texts separately.
        Changes are wrapped in <span> tags with inline styles.
        
        Args:
            original: Original JD text
            refined: Refined JD text
            
        Returns:
            Tuple of (marked_original, marked_refined, statistics)
        """
        # Split into lines for line-by-line comparison
        original_lines = original.splitlines()
        refined_lines = refined.splitlines()
        
        # Use SequenceMatcher to find line-level changes
        seq_matcher = SequenceMatcher(None, original_lines, refined_lines)
        
        marked_original_lines = []
        marked_refined_lines = []
        
        for tag, i1, i2, j1, j2 in seq_matcher.get_opcodes():
            if tag == 'equal':
                # Lines are the same
                marked_original_lines.extend(original_lines[i1:i2])
                marked_refined_lines.extend(refined_lines[j1:j2])
                
            elif tag == 'delete':
                # Lines deleted from original
                for line in original_lines[i1:i2]:
                    marked_line = f'<span class="diff-deleted" style="background-color: #ffcccc; text-decoration: line-through;">{JDInlineDiffGenerator._escape_html(line)}</span>'
                    marked_original_lines.append(marked_line)
                    
            elif tag == 'insert':
                # Lines added in refined
                for line in refined_lines[j1:j2]:
                    marked_line = f'<span class="diff-added" style="background-color: #ccffcc;">{JDInlineDiffGenerator._escape_html(line)}</span>'
                    marked_refined_lines.append(marked_line)
                    
            elif tag == 'replace':
                # Lines changed - do word-level diff
                orig_section = original_lines[i1:i2]
                ref_section = refined_lines[j1:j2]
                
                # Word-level diff for changed lines
                marked_orig, marked_ref = JDInlineDiffGenerator._word_level_diff(
                    '\n'.join(orig_section),
                    '\n'.join(ref_section)
                )
                
                marked_original_lines.extend(marked_orig.split('\n'))
                marked_refined_lines.extend(marked_ref.split('\n'))
        
        # Join lines back together
        marked_original = '\n'.join(marked_original_lines)
        marked_refined = '\n'.join(marked_refined_lines)
        
        # Calculate statistics
        stats = JDInlineDiffGenerator._calculate_stats(original, refined)
        
        return marked_original, marked_refined, stats
    
    @staticmethod
    def _word_level_diff(original: str, refined: str) -> Tuple[str, str]:
        """
        Perform word-level diff for changed sections.
        
        Returns:
            Tuple of (marked_original, marked_refined)
        """
        original_words = original.split()
        refined_words = refined.split()
        
        matcher = SequenceMatcher(None, original_words, refined_words)
        
        marked_original = []
        marked_refined = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                words = ' '.join(original_words[i1:i2])
                marked_original.append(JDInlineDiffGenerator._escape_html(words))
                marked_refined.append(JDInlineDiffGenerator._escape_html(words))
                
            elif tag == 'delete':
                deleted = ' '.join(original_words[i1:i2])
                marked_original.append(
                    f'<span class="diff-deleted" style="background-color: #ffcccc; text-decoration: line-through;">{JDInlineDiffGenerator._escape_html(deleted)}</span>'
                )
                
            elif tag == 'insert':
                inserted = ' '.join(refined_words[j1:j2])
                marked_refined.append(
                    f'<span class="diff-added" style="background-color: #ccffcc;">{JDInlineDiffGenerator._escape_html(inserted)}</span>'
                )
                
            elif tag == 'replace':
                deleted = ' '.join(original_words[i1:i2])
                inserted = ' '.join(refined_words[j1:j2])
                
                marked_original.append(
                    f'<span class="diff-modified" style="background-color: #fff3cd;">{JDInlineDiffGenerator._escape_html(deleted)}</span>'
                )
                marked_refined.append(
                    f'<span class="diff-modified" style="background-color: #d4edda;">{JDInlineDiffGenerator._escape_html(inserted)}</span>'
                )
        
        return ' '.join(marked_original), ' '.join(marked_refined)
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    @staticmethod
    def _calculate_stats(original: str, refined: str) -> Dict[str, int]:
        """Calculate change statistics"""
        matcher = SequenceMatcher(None, original, refined)
        
        additions = 0
        deletions = 0
        modifications = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'insert':
                additions += (j2 - j1)
            elif tag == 'delete':
                deletions += (i2 - i1)
            elif tag == 'replace':
                modifications += max(i2 - i1, j2 - j1)
        
        # Calculate word-level stats
        original_words = len(original.split())
        refined_words = len(refined.split())
        
        return {
            'original_length': len(original),
            'refined_length': len(refined),
            'original_words': original_words,
            'refined_words': refined_words,
            'characters_added': additions,
            'characters_deleted': deletions,
            'characters_modified': modifications,
            'total_changes': additions + deletions + modifications,
            'similarity_ratio': round(matcher.ratio() * 100, 2)
        }