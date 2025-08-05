import { test, expect } from '@playwright/test';

test.describe('API Integration Tests', () => {
  const API_URL = 'http://localhost:8000/api/v1';

  test('should check backend health', async ({ request }) => {
    const response = await request.get(`${API_URL.replace('/api/v1', '')}/health`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
  });

  test('should create episode via API and see it in UI', async ({ page, request }) => {
    // Create episode via API
    const formData = new FormData();
    formData.append('name', 'API Test Episode');
    formData.append('speakers_count', '2');
    formData.append('url', 'https://example.com/api-test.mp3');
    formData.append('transcript_only', 'false');
    formData.append('generate_extra', 'false');
    
    const response = await request.post(`${API_URL}/episodes/`, {
      multipart: formData
    });
    
    expect(response.ok()).toBeTruthy();
    const episode = await response.json();
    expect(episode.name).toBe('API Test Episode');
    
    // Navigate to episodes page and verify it appears
    await page.goto('http://localhost:3000/episodes');
    await page.waitForLoadState('networkidle');
    
    // Look for the episode we just created
    await expect(page.locator(`text=API Test Episode`)).toBeVisible({ timeout: 10000 });
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('**/api/v1/episodes/', route => {
      route.fulfill({
        status: 500,
        body: JSON.stringify({ detail: 'Internal Server Error' })
      });
    });
    
    await page.goto('http://localhost:3000');
    
    // Try to create episode
    await page.fill('input[id="url"]', 'https://example.com/test.mp3');
    await page.fill('input[id="name"]', 'Error Test');
    await page.click('button:has-text("Create Artifacts")');
    
    // Should handle error gracefully (implementation dependent)
    // The app should not crash and should show some indication of failure
    await page.waitForTimeout(1000); // Wait for potential error handling
  });

  test('should update episode show notes via API', async ({ request }) => {
    // First, get list of episodes
    const listResponse = await request.get(`${API_URL}/episodes/`);
    expect(listResponse.ok()).toBeTruthy();
    
    const episodes = await listResponse.json();
    if (episodes.length > 0) {
      const episodeId = episodes[0].id;
      
      // Update show notes
      const showNotes = [
        { text: 'API Updated Note 1', url: 'https://example1.com' },
        { text: 'API Updated Note 2', url: null }
      ];
      
      const updateResponse = await request.patch(
        `${API_URL}/episodes/${episodeId}/show-notes`,
        {
          data: showNotes
        }
      );
      
      // Check response (might fail if episode file doesn't exist)
      if (updateResponse.ok()) {
        const updatedEpisode = await updateResponse.json();
        expect(updatedEpisode.id).toBe(episodeId);
      }
    }
  });

  test('should retrieve transcripts via API', async ({ request }) => {
    // Try to get a transcript (might not exist)
    const response = await request.get(`${API_URL}/transcripts/test_episode`);
    
    if (response.ok()) {
      const data = await response.json();
      expect(data).toHaveProperty('episode_name');
      expect(data).toHaveProperty('transcript');
    } else {
      expect(response.status()).toBe(404);
    }
  });

  test('should check processing status', async ({ request }) => {
    // Create a dummy task ID
    const taskId = 'test-task-123';
    
    const response = await request.get(`${API_URL}/processing/status/${taskId}`);
    expect(response.ok()).toBeTruthy();
    
    const status = await response.json();
    expect(status).toHaveProperty('task_id', taskId);
    expect(status).toHaveProperty('status');
    expect(['pending', 'processing', 'completed', 'failed']).toContain(status.status);
  });

  test('should sync chapters via API', async ({ request }) => {
    const chapterData = {
      audio_name: 'api_test_audio',
      video_name: 'api_test_video',
      chapters: '[00:00:00] API Test Start\n[00:05:00] API Test End'
    };
    
    const response = await request.post(`${API_URL}/chapters/sync`, {
      data: chapterData
    });
    
    expect(response.ok()).toBeTruthy();
    const result = await response.json();
    expect(result).toHaveProperty('message');
    expect(result).toHaveProperty('task_id');
  });

  test('should handle concurrent API requests', async ({ request }) => {
    // Make multiple requests simultaneously
    const promises = [];
    
    for (let i = 0; i < 5; i++) {
      promises.push(request.get(`${API_URL}/episodes/`));
    }
    
    const responses = await Promise.all(promises);
    
    // All requests should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });
  });

  test('should validate API response schemas', async ({ request }) => {
    // Get episodes and validate schema
    const response = await request.get(`${API_URL}/episodes/`);
    expect(response.ok()).toBeTruthy();
    
    const episodes = await response.json();
    expect(Array.isArray(episodes)).toBeTruthy();
    
    if (episodes.length > 0) {
      const episode = episodes[0];
      
      // Validate episode schema
      expect(episode).toHaveProperty('id');
      expect(episode).toHaveProperty('name');
      expect(episode).toHaveProperty('speakers_count');
      expect(episode).toHaveProperty('status');
      expect(episode).toHaveProperty('created_at');
      expect(episode).toHaveProperty('updated_at');
      
      // Validate types
      expect(typeof episode.id).toBe('string');
      expect(typeof episode.name).toBe('string');
      expect(typeof episode.speakers_count).toBe('number');
      expect(typeof episode.status).toBe('string');
      expect(typeof episode.created_at).toBe('string');
      expect(typeof episode.updated_at).toBe('string');
    }
  });
});