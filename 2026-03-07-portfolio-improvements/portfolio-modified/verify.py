#!/usr/bin/env python3
"""
Quick verification that the portfolio accessibility enhancements are present.
"""
import os
import sys

def check_file(path, description, *patterns):
    """Check that each pattern appears in the file at path."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ {description}: file not found at {path}")
        return False
    
    all_ok = True
    for pattern in patterns:
        if pattern in content:
            print(f"✅ {description}: found '{pattern[:30]}...'")
        else:
            print(f"❌ {description}: missing '{pattern[:30]}...'")
            all_ok = False
    return all_ok

def main():
    base = os.path.dirname(__file__)
    ok = True
    
    # HTML checks
    html_path = os.path.join(base, 'index.html')
    ok &= check_file(html_path, 'Skip link in HTML',
                     'class="skip-link"',
                     'Skip to main content',
                     'id="main"')
    ok &= check_file(html_path, 'Back-to-top button in HTML',
                     'id="back-to-top"',
                     'class="back-to-top"',
                     'aria-label="Back to top"')
    
    # CSS checks
    css_path = os.path.join(base, 'styles.css')
    ok &= check_file(css_path, 'Skip link styles',
                     '.skip-link {',
                     '.skip-link:focus')
    ok &= check_file(css_path, 'Back-to-top styles',
                     '.back-to-top {',
                     '.back-to-top.visible')
    ok &= check_file(css_path, 'Print rule includes new elements',
                     '.skip-link,',
                     '.back-to-top {')
    
    # JS checks
    js_path = os.path.join(base, 'script.js')
    ok &= check_file(js_path, 'Back-to-top JavaScript',
                     'const backToTop = document.getElementById',
                     'backToTop.classList.add',
                     'window.scrollTo({ top: 0, behavior: \'smooth\' })')
    
    if ok:
        print('\n🎉 All checks passed.')
        sys.exit(0)
    else:
        print('\n⚠️  Some checks failed. Please review the changes.')
        sys.exit(1)

if __name__ == '__main__':
    main()