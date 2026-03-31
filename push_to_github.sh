#!/bin/bash

echo "Pushing to GitHub..."
echo "Repository: https://github.com/ai-azure-agentic-va/ai-agent-eval-testing.git"
echo ""

# Switch back to HTTPS
git remote set-url origin https://github.com/ai-azure-agentic-va/ai-agent-eval-testing.git

# Push to GitHub
echo "You will be prompted for:"
echo "  Username: your GitHub username"
echo "  Password: your Personal Access Token (not your actual password)"
echo ""

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "View your repository at: https://github.com/ai-azure-agentic-va/ai-agent-eval-testing"
else
    echo ""
    echo "❌ Push failed. Make sure you have:"
    echo "   1. A valid Personal Access Token with 'repo' scope"
    echo "   2. Access to the repository"
fi
