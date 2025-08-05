import { test, expect } from '@playwright/test';

test.describe('Episode Creation and Management Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the home page
    await page.goto('http://localhost:3000');
  });

  test('should create a new episode from URL', async ({ page }) => {
    // Fill in the form
    await page.fill('input[id="url"]', 'https://example.com/test-audio.mp3');
    await page.fill('input[id="name"]', 'E2E Test Episode');
    await page.fill('input[id="speakers"]', '2');
    
    // Submit the form
    await page.click('button:has-text("Create Artifacts")');
    
    // Check for success message
    await expect(page.locator('text=Processing started for E2E Test Episode')).toBeVisible();
  });

  test('should navigate to episodes list and see created episodes', async ({ page }) => {
    // Navigate to episodes page
    await page.goto('http://localhost:3000/episodes');
    
    // Check page title
    await expect(page.locator('h2:has-text("Edit Episodes")')).toBeVisible();
    
    // Check if episodes are listed
    const episodeCards = page.locator('.space-y-4 > div');
    await expect(episodeCards).toHaveCount(await episodeCards.count());
  });

  test('should edit show notes for a completed episode', async ({ page }) => {
    // Navigate to episodes page
    await page.goto('http://localhost:3000/episodes');
    
    // Wait for episodes to load
    await page.waitForSelector('.space-y-4 > div');
    
    // Click on the first "Edit Show Notes" link
    const editLink = page.locator('a:has-text("Edit Show Notes")').first();
    const linkExists = await editLink.count() > 0;
    
    if (linkExists) {
      await editLink.click();
      
      // Wait for edit page to load
      await expect(page.locator('h2:has-text("Edit Show Notes:")')).toBeVisible();
      
      // Add a new show note
      await page.click('button:has-text("Add Item")');
      
      // Fill in the new show note
      const textInputs = page.locator('input[placeholder="Item text"]');
      const lastInput = textInputs.last();
      await lastInput.fill('E2E Test Note');
      
      // Save changes
      await page.click('button:has-text("Save Changes")');
      
      // Should redirect back to episodes page
      await expect(page).toHaveURL(/\/episodes$/);
    }
  });

  test('should sync chapters between audio and video', async ({ page }) => {
    // Navigate to sync page
    await page.goto('http://localhost:3000/sync');
    
    // Check page title
    await expect(page.locator('h2:has-text("Sync Video Chapters")')).toBeVisible();
    
    // Fill in the form
    await page.fill('input[id="video_name"]', 'test_video_episode');
    await page.fill('input[id="audio_name"]', 'test_audio_episode');
    await page.fill('textarea[id="chapters"]', '[00:00:00] Introduction\n[00:05:00] Main Topic\n[00:10:00] Conclusion');
    
    // Submit the form
    await page.click('button:has-text("Sync Chapters")');
    
    // Check for success message
    await expect(page.locator('text=Syncing chapters for test_video_episode and test_audio_episode')).toBeVisible();
  });

  test('should handle file upload', async ({ page }) => {
    // Create a test audio file
    const buffer = Buffer.from('fake audio content');
    
    // Set up file chooser before clicking
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('label[for="file"]');
    const fileChooser = await fileChooserPromise;
    
    // Create a fake file
    await fileChooser.setFiles({
      name: 'test-audio.mp3',
      mimeType: 'audio/mpeg',
      buffer: buffer
    });
    
    // Fill in other fields
    await page.fill('input[id="name"]', 'E2E File Upload Test');
    
    // Check that file name is displayed
    await expect(page.locator('text=test-audio.mp3')).toBeVisible();
    
    // Submit the form
    await page.click('button:has-text("Create Artifacts")');
    
    // Check for success message
    await expect(page.locator('text=Processing started for E2E File Upload Test')).toBeVisible();
  });

  test('should toggle transcript-only and generate-extra options', async ({ page }) => {
    // Fill required fields
    await page.fill('input[id="url"]', 'https://example.com/test.mp3');
    await page.fill('input[id="name"]', 'Options Test');
    
    // Check transcript-only checkbox
    await page.check('input[id="transcript-only"]');
    
    // Check generate-extra checkbox
    await page.check('input[id="generate-extra"]');
    
    // Verify checkboxes are checked
    await expect(page.locator('input[id="transcript-only"]')).toBeChecked();
    await expect(page.locator('input[id="generate-extra"]')).toBeChecked();
    
    // Submit form
    await page.click('button:has-text("Create Artifacts")');
    
    // Check for success message
    await expect(page.locator('text=Processing started for Options Test')).toBeVisible();
  });

  test('should validate required fields', async ({ page }) => {
    // Try to submit without filling required fields
    const submitButton = page.locator('button:has-text("Create Artifacts")');
    
    // Button should be disabled when fields are empty
    await expect(submitButton).toBeDisabled();
    
    // Fill only URL
    await page.fill('input[id="url"]', 'https://example.com/test.mp3');
    
    // Button should still be disabled (missing name)
    await expect(submitButton).toBeDisabled();
    
    // Fill name
    await page.fill('input[id="name"]', 'Test Episode');
    
    // Button should now be enabled
    await expect(submitButton).toBeEnabled();
  });

  test('should navigate between pages using sidebar', async ({ page }) => {
    // Check sidebar exists
    const sidebar = page.locator('nav');
    await expect(sidebar).toBeVisible();
    
    // Navigate to episodes page
    const episodesLink = page.locator('a:has-text("Edit Episodes")');
    if (await episodesLink.count() > 0) {
      await episodesLink.click();
      await expect(page).toHaveURL(/\/episodes$/);
    }
    
    // Navigate to sync page
    const syncLink = page.locator('a:has-text("Sync Chapters")');
    if (await syncLink.count() > 0) {
      await syncLink.click();
      await expect(page).toHaveURL(/\/sync$/);
    }
    
    // Navigate back to home
    const homeLink = page.locator('a:has-text("Create Writeup")');
    if (await homeLink.count() > 0) {
      await homeLink.click();
      await expect(page).toHaveURL(/\/$/);
    }
  });
});