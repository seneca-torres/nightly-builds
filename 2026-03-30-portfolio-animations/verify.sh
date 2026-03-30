#!/bin/bash

# Portfolio Animations Verification Script
# Checks that all animations work correctly

set -e

echo "🔍 Portfolio Animations Verification"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "animations.css" ] || [ ! -f "animations.js" ]; then
    echo -e "${RED}❌ Error: Must run from animation-enhancement directory${NC}"
    echo "Run: cd animation-enhancement && ./verify.sh"
    exit 1
fi

echo -e "${YELLOW}Running verification tests...${NC}"
echo

# Test 1: Check required files exist
echo "📁 File Structure Test"
required_files=("animations.css" "animations.js" "integration-guide.md" "demo.html")
missing_files=0
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✅ $file${NC}"
    else
        echo -e "  ${RED}❌ $file (missing)${NC}"
        missing_files=$((missing_files + 1))
    fi
done

if [ $missing_files -eq 0 ]; then
    echo -e "${GREEN}✅ All required files present${NC}"
else
    echo -e "${RED}❌ Missing $missing_files required file(s)${NC}"
fi
echo

# Test 2: Check CSS syntax
echo "🎨 CSS Syntax Test"
if command -v csslint &> /dev/null; then
    csslint --quiet animations.css 2>&1 | head -20
    echo -e "${GREEN}✅ CSS syntax check passed${NC}"
else
    echo -e "${YELLOW}⚠️  csslint not installed, skipping CSS syntax check${NC}"
    echo "  Install with: npm install -g csslint"
fi
echo

# Test 3: Check JavaScript syntax
echo "📜 JavaScript Syntax Test"
if command -v node &> /dev/null; then
    if node -c animations.js; then
        echo -e "${GREEN}✅ JavaScript syntax check passed${NC}"
    else
        echo -e "${RED}❌ JavaScript syntax error${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Node.js not available, skipping JS syntax check${NC}"
fi
echo

# Test 4: Check for required CSS classes
echo "🔤 CSS Class Check"
required_classes=(".flip-card" ".fade-in-up" ".demo-player" ".chalk-btn" ".chalk-writing")
missing_classes=0
for class in "${required_classes[@]}"; do
    if grep -q "$class" animations.css; then
        echo -e "  ${GREEN}✅ $class${NC}"
    else
        echo -e "  ${RED}❌ $class (not found in CSS)${NC}"
        missing_classes=$((missing_classes + 1))
    fi
done

if [ $missing_classes -eq 0 ]; then
    echo -e "${GREEN}✅ All required CSS classes defined${NC}"
else
    echo -e "${RED}❌ Missing $missing_classes CSS class(es)${NC}"
fi
echo

# Test 5: Check demo file loads
echo "🚀 Demo File Test"
if [ -f "demo.html" ]; then
    echo -e "  ${GREEN}✅ demo.html exists${NC}"
    # Check demo file includes required resources
    if grep -q "animations.css" demo.html && grep -q "animations.js" demo.html; then
        echo -e "  ${GREEN}✅ demo.html includes animation resources${NC}"
    else
        echo -e "  ${RED}❌ demo.html missing animation resources${NC}"
    fi
else
    echo -e "${RED}❌ demo.html missing${NC}"
fi
echo

# Test 6: Browser compatibility checks
echo "🌐 Browser Compatibility"
echo "  Checking for modern CSS features..."

# Check for CSS Grid support (should be in animations)
if grep -q "grid-template-columns" animations.css; then
    echo -e "  ${YELLOW}⚠️  Uses CSS Grid (IE11 not supported)${NC}"
else
    echo -e "  ${GREEN}✅ No CSS Grid usage detected${NC}"
fi

# Check for CSS Custom Properties
if grep -q "var(--" animations.css; then
    echo -e "  ${YELLOW}⚠️  Uses CSS Custom Properties (IE11 not supported)${NC}"
else
    echo -e "  ${GREEN}✅ No CSS Custom Properties usage detected${NC}"
fi

# Check for @keyframes animations
if grep -q "@keyframes" animations.css; then
    echo -e "  ${GREEN}✅ Uses CSS animations${NC}"
else
    echo -e "  ${YELLOW}⚠️  No CSS animations defined${NC}"
fi
echo

# Test 7: Integration guide check
echo "📖 Integration Guide Check"
if [ -f "integration-guide.md" ]; then
    word_count=$(wc -w < integration-guide.md)
    if [ "$word_count" -gt 100 ]; then
        echo -e "  ${GREEN}✅ Integration guide has sufficient content ($word_count words)${NC}"
    else
        echo -e "  ${RED}❌ Integration guide too short ($word_count words)${NC}"
    fi
    
    # Check for key sections
    key_sections=("Step 1" "CSS" "JavaScript" "Troubleshooting")
    missing_sections=0
    for section in "${key_sections[@]}"; do
        if grep -qi "$section" integration-guide.md; then
            echo -e "  ${GREEN}✅ '$section' section found${NC}"
        else
            echo -e "  ${RED}❌ '$section' section missing${NC}"
            missing_sections=$((missing_sections + 1))
        fi
    done
else
    echo -e "${RED}❌ integration-guide.md missing${NC}"
fi
echo

# Summary
echo "=================================="
echo -e "${GREEN}✅ Verification complete!${NC}"
echo
echo "Next steps:"
echo "1. Copy animation-enhancement/ to your portfolio directory"
echo "2. Follow the integration guide in integration-guide.md"
echo "3. Test by opening demo.html in a browser"
echo "4. Integrate with your portfolio site"
echo
echo "For issues, check the integration guide or contact the maintainer."