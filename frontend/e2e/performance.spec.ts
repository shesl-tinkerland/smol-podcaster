import { test, expect } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('should load home page within acceptable time', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto('http://localhost:3000');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 3 seconds
    expect(loadTime).toBeLessThan(3000);
  });

  test('should render episode list efficiently', async ({ page }) => {
    await page.goto('http://localhost:3000/episodes');
    
    // Measure time to render episodes
    const startTime = Date.now();
    await page.waitForSelector('.space-y-4 > div', { timeout: 5000 });
    const renderTime = Date.now() - startTime;
    
    // Should render within 2 seconds
    expect(renderTime).toBeLessThan(2000);
  });

  test('should handle form submission without lag', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Fill form
    await page.fill('input[id="url"]', 'https://example.com/perf-test.mp3');
    await page.fill('input[id="name"]', 'Performance Test');
    
    // Measure submission time
    const startTime = Date.now();
    await page.click('button:has-text("Create Artifacts")');
    
    // Wait for success message or redirect
    await page.waitForSelector('text=Processing started', { timeout: 2000 }).catch(() => {
      // If no success message, that's okay for this test
    });
    
    const submitTime = Date.now() - startTime;
    
    // Submission should be responsive (under 1 second)
    expect(submitTime).toBeLessThan(1000);
  });

  test('should handle large episode lists', async ({ page, request }) => {
    // Mock API to return many episodes
    await page.route('**/api/v1/episodes/', route => {
      const episodes = Array.from({ length: 100 }, (_, i) => ({
        id: `perf-${i}`,
        name: `Performance Episode ${i}`,
        speakers_count: 2,
        status: 'completed',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }));
      
      route.fulfill({
        status: 200,
        body: JSON.stringify(episodes)
      });
    });
    
    const startTime = Date.now();
    await page.goto('http://localhost:3000/episodes');
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Should handle 100 episodes efficiently
    expect(loadTime).toBeLessThan(5000);
    
    // Check that episodes are rendered
    const episodeCards = page.locator('.space-y-4 > div');
    const count = await episodeCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should have acceptable input lag', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    const input = page.locator('input[id="name"]');
    
    // Type quickly and measure response
    const testText = 'This is a performance test for input lag';
    const startTime = Date.now();
    
    await input.type(testText, { delay: 10 }); // Type with minimal delay
    
    const typeTime = Date.now() - startTime;
    const expectedMinTime = testText.length * 10; // Minimum based on delay
    const acceptableMaxTime = expectedMinTime * 2; // Allow up to 2x for processing
    
    expect(typeTime).toBeLessThanOrEqual(acceptableMaxTime);
    
    // Verify all text was entered
    const value = await input.inputValue();
    expect(value).toBe(testText);
  });

  test('should navigate between pages quickly', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Measure navigation time to episodes page
    const navStartTime = Date.now();
    await page.goto('http://localhost:3000/episodes');
    await page.waitForLoadState('networkidle');
    const episodesLoadTime = Date.now() - navStartTime;
    
    // Measure navigation time to sync page
    const syncStartTime = Date.now();
    await page.goto('http://localhost:3000/sync');
    await page.waitForLoadState('networkidle');
    const syncLoadTime = Date.now() - syncStartTime;
    
    // Both navigations should be quick
    expect(episodesLoadTime).toBeLessThan(2000);
    expect(syncLoadTime).toBeLessThan(2000);
  });

  test('should handle rapid form interactions', async ({ page }) => {
    await page.goto('http://localhost:3000/sync');
    
    // Rapidly fill and clear fields
    const videoInput = page.locator('input[id="video_name"]');
    const audioInput = page.locator('input[id="audio_name"]');
    const chaptersTextarea = page.locator('textarea[id="chapters"]');
    
    for (let i = 0; i < 10; i++) {
      await videoInput.fill(`video_${i}`);
      await audioInput.fill(`audio_${i}`);
      await chaptersTextarea.fill(`[00:0${i}:00] Chapter ${i}`);
    }
    
    // Verify final values
    expect(await videoInput.inputValue()).toBe('video_9');
    expect(await audioInput.inputValue()).toBe('audio_9');
    expect(await chaptersTextarea.inputValue()).toContain('Chapter 9');
  });

  test('should maintain performance with multiple checkboxes', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    const transcriptCheckbox = page.locator('input[id="transcript-only"]');
    const generateCheckbox = page.locator('input[id="generate-extra"]');
    
    // Rapidly toggle checkboxes
    const startTime = Date.now();
    
    for (let i = 0; i < 20; i++) {
      await transcriptCheckbox.click();
      await generateCheckbox.click();
    }
    
    const toggleTime = Date.now() - startTime;
    
    // Should handle rapid toggling efficiently
    expect(toggleTime).toBeLessThan(2000);
    
    // Verify final state (clicked even number of times, so should be unchecked)
    expect(await transcriptCheckbox.isChecked()).toBe(false);
    expect(await generateCheckbox.isChecked()).toBe(false);
  });
});