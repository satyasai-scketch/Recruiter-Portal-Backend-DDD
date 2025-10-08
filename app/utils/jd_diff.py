from difflib import HtmlDiff
from typing import Dict, Tuple
import re


class JDDiffGenerator:
    """Generate HTML diff between original and refined JD texts"""
    
    @staticmethod
    def generate_diff(original: str, refined: str) -> Tuple[str, Dict[str, int]]:
        """
        Generate HTML diff with change statistics.
        
        Args:
            original: Original JD text
            refined: Refined JD text
            
        Returns:
            Tuple of (html_diff, statistics)
        """
        # Split texts into lines for better diff
        original_lines = original.splitlines(keepends=True)
        refined_lines = refined.splitlines(keepends=True)
        
        # Create HtmlDiff instance with custom styling
        differ = HtmlDiff(
            tabsize=4,
            wrapcolumn=80
        )
        
        # Generate diff table
        diff_html = differ.make_table(
            original_lines,
            refined_lines,
            fromdesc="Original JD",
            todesc="Refined JD",
            context=True,  # Show context around changes
            numlines=2  # Number of context lines
        )
        
        # Calculate statistics
        stats = JDDiffGenerator._calculate_stats(original, refined)
        
        # Add custom CSS to make it more readable
        styled_html = JDDiffGenerator._add_custom_styles(diff_html)
        
        return styled_html, stats
    
    @staticmethod
    def generate_inline_diff(original: str, refined: str) -> Tuple[str, Dict[str, int]]:
        """
        Generate inline (side-by-side) HTML diff.
        
        Returns HTML with original and refined side by side with highlighting.
        """
        original_lines = original.splitlines()
        refined_lines = refined.splitlines()
        
        differ = HtmlDiff(tabsize=4)
        
        # Generate inline diff (side-by-side view)
        diff_html = differ.make_file(
            original_lines,
            refined_lines,
            fromdesc="Original JD",
            todesc="Refined JD",
            context=True,
            numlines=3
        )
        
        stats = JDDiffGenerator._calculate_stats(original, refined)
        styled_html = JDDiffGenerator._add_custom_styles(diff_html)
        
        return styled_html, stats
    
    @staticmethod
    def generate_simple_diff(original: str, refined: str) -> str:
        """
        Generate simple marked-up text with inline HTML tags.
        
        Returns plain text with <ins> and <del> tags.
        """
        from difflib import SequenceMatcher
        
        # Use SequenceMatcher for word-level diff
        original_words = original.split()
        refined_words = refined.split()
        
        matcher = SequenceMatcher(None, original_words, refined_words)
        result = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                result.append(' '.join(original_words[i1:i2]))
            elif tag == 'delete':
                deleted = ' '.join(original_words[i1:i2])
                result.append(f'<del style="background-color: #ffcccc; text-decoration: line-through;">{deleted}</del>')
            elif tag == 'insert':
                inserted = ' '.join(refined_words[j1:j2])
                result.append(f'<ins style="background-color: #ccffcc; text-decoration: none;">{inserted}</ins>')
            elif tag == 'replace':
                deleted = ' '.join(original_words[i1:i2])
                inserted = ' '.join(refined_words[j1:j2])
                result.append(f'<del style="background-color: #ffcccc; text-decoration: line-through;">{deleted}</del>')
                result.append(f'<ins style="background-color: #ccffcc; text-decoration: none;">{inserted}</ins>')
        
        return ' '.join(result)
    
    @staticmethod
    def _calculate_stats(original: str, refined: str) -> Dict[str, int]:
        """Calculate change statistics"""
        from difflib import SequenceMatcher
        
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
    
    @staticmethod
    def _add_custom_styles(html: str) -> str:
        """Add custom CSS styling to diff HTML"""
        
        custom_css = """
        <style>
            /* Diff table styling */
            table.diff {
                font-family: 'Courier New', monospace;
                border-collapse: collapse;
                width: 100%;
                font-size: 14px;
            }
            
            table.diff thead {
                background-color: #f5f5f5;
                font-weight: bold;
            }
            
            table.diff tbody th {
                background-color: #f9f9f9;
                text-align: right;
                padding: 2px 8px;
                width: 40px;
                color: #666;
            }
            
            table.diff td {
                padding: 4px 8px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            /* Deletion styling */
            table.diff .diff_chg {
                background-color: #fff3cd;
                color: #856404;
            }
            
            table.diff .diff_sub {
                background-color: #ffcccc;
                color: #c00;
            }
            
            /* Addition styling */
            table.diff .diff_add {
                background-color: #ccffcc;
                color: #080;
            }
            
            /* Header styling */
            table.diff th.diff_next {
                background-color: #e0e0e0;
            }
            
            /* Make it responsive */
            @media (max-width: 768px) {
                table.diff {
                    font-size: 12px;
                }
                table.diff td {
                    padding: 2px 4px;
                }
            }
        </style>
        """
        
        # Insert CSS before closing </head> or at beginning if no head
        if '</head>' in html:
            html = html.replace('</head>', f'{custom_css}</head>')
        else:
            html = custom_css + html
        
        return html