# git-helper.ps1

# Step 1: Add all changes
$confirm = Read-Host "Run 'git add .' ? (y/n)"
if ($confirm -eq 'y') {
    git add .
}

# Step 2: Git status
$confirm = Read-Host "Run 'git status' ? (y/n)"
if ($confirm -eq 'y') {
    git status
}

# Step 3: Commit
$confirm = Read-Host "Run 'git commit' ? (y/n)"
if ($confirm -eq 'y') {
    $message = Read-Host "Enter commit message"
    git commit -m "$message"
}

# Step 4: Set branch to main (first time only)
$confirm = Read-Host "Run 'git branch -M main' ? (y/n)"
if ($confirm -eq 'y') {
    git branch -M main
}

# Step 5: Push
$confirm = Read-Host "Run 'git push -u origin main' ? (y/n)"
if ($confirm -eq 'y') {
    git push -u origin main
}
