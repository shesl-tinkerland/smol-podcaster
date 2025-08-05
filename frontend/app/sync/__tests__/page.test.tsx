import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import SyncPage from '../page';
import { chapterApi } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  chapterApi: {
    sync: jest.fn()
  }
}));

// Mock the Sidebar component
jest.mock('@/components/sidebar', () => ({
  Sidebar: () => <div>Sidebar</div>
}));

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

describe('SyncPage', () => {
  let queryClient: QueryClient;
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    queryClient = createQueryClient();
    user = userEvent.setup();
    jest.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );

  it('renders the page title', () => {
    render(<SyncPage />, { wrapper });
    expect(screen.getByText('Sync Video Chapters')).toBeInTheDocument();
  });

  it('renders all form fields', () => {
    render(<SyncPage />, { wrapper });
    
    expect(screen.getByLabelText('Video File Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Audio File Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Chapters')).toBeInTheDocument();
  });

  it('disables submit button when fields are empty', () => {
    render(<SyncPage />, { wrapper });
    
    const submitButton = screen.getByRole('button', { name: 'Sync Chapters' });
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when all fields are filled', async () => {
    render(<SyncPage />, { wrapper });
    
    const videoInput = screen.getByLabelText('Video File Name');
    const audioInput = screen.getByLabelText('Audio File Name');
    const chaptersTextarea = screen.getByLabelText('Chapters');
    
    await user.type(videoInput, 'video_episode');
    await user.type(audioInput, 'audio_episode');
    await user.type(chaptersTextarea, '[00:00:00] Introduction\n[00:05:00] Main Topic');
    
    const submitButton = screen.getByRole('button', { name: 'Sync Chapters' });
    expect(submitButton).toBeEnabled();
  });

  it('submits form with correct data', async () => {
    const mockResponse = {
      message: 'Syncing chapters for video_episode and audio_episode',
      task_id: 'sync-task-123'
    };

    (chapterApi.sync as jest.Mock).mockResolvedValue(mockResponse);

    render(<SyncPage />, { wrapper });
    
    const videoInput = screen.getByLabelText('Video File Name');
    const audioInput = screen.getByLabelText('Audio File Name');
    const chaptersTextarea = screen.getByLabelText('Chapters');
    
    await user.type(videoInput, 'video_episode');
    await user.type(audioInput, 'audio_episode');
    await user.type(chaptersTextarea, '[00:00:00] Introduction\n[00:05:00] Main Topic');
    
    const submitButton = screen.getByRole('button', { name: 'Sync Chapters' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(chapterApi.sync).toHaveBeenCalledWith({
        video_name: 'video_episode',
        audio_name: 'audio_episode',
        chapters: '[00:00:00] Introduction\n[00:05:00] Main Topic'
      });
    });
  });

  it('shows success message after successful submission', async () => {
    const mockResponse = {
      message: 'Syncing chapters for video_episode and audio_episode',
      task_id: 'sync-task-123'
    };

    (chapterApi.sync as jest.Mock).mockResolvedValue(mockResponse);

    render(<SyncPage />, { wrapper });
    
    const videoInput = screen.getByLabelText('Video File Name');
    const audioInput = screen.getByLabelText('Audio File Name');
    const chaptersTextarea = screen.getByLabelText('Chapters');
    
    await user.type(videoInput, 'video_episode');
    await user.type(audioInput, 'audio_episode');
    await user.type(chaptersTextarea, '[00:00:00] Introduction');
    
    const submitButton = screen.getByRole('button', { name: 'Sync Chapters' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Syncing chapters for video_episode and audio_episode')).toBeInTheDocument();
    });
  });

  it('resets form after successful submission', async () => {
    const mockResponse = {
      message: 'Syncing chapters for video_episode and audio_episode',
      task_id: 'sync-task-123'
    };

    (chapterApi.sync as jest.Mock).mockResolvedValue(mockResponse);

    render(<SyncPage />, { wrapper });
    
    const videoInput = screen.getByLabelText('Video File Name') as HTMLInputElement;
    const audioInput = screen.getByLabelText('Audio File Name') as HTMLInputElement;
    const chaptersTextarea = screen.getByLabelText('Chapters') as HTMLTextAreaElement;
    
    await user.type(videoInput, 'video_episode');
    await user.type(audioInput, 'audio_episode');
    await user.type(chaptersTextarea, '[00:00:00] Introduction');
    
    const submitButton = screen.getByRole('button', { name: 'Sync Chapters' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(videoInput.value).toBe('');
      expect(audioInput.value).toBe('');
      expect(chaptersTextarea.value).toBe('');
    });
  });

  it('shows loading state during submission', async () => {
    (chapterApi.sync as jest.Mock).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    render(<SyncPage />, { wrapper });
    
    const videoInput = screen.getByLabelText('Video File Name');
    const audioInput = screen.getByLabelText('Audio File Name');
    const chaptersTextarea = screen.getByLabelText('Chapters');
    
    await user.type(videoInput, 'video_episode');
    await user.type(audioInput, 'audio_episode');
    await user.type(chaptersTextarea, '[00:00:00] Introduction');
    
    const submitButton = screen.getByRole('button', { name: 'Sync Chapters' });
    await user.click(submitButton);
    
    expect(screen.getByRole('button', { name: 'Syncing...' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Syncing...' })).toBeDisabled();
  });

  it('displays placeholder text in chapters textarea', () => {
    render(<SyncPage />, { wrapper });
    
    const chaptersTextarea = screen.getByLabelText('Chapters');
    expect(chaptersTextarea).toHaveAttribute('placeholder', expect.stringContaining('[00:00:00] Introduction'));
  });

  it('allows multiline input in chapters textarea', async () => {
    render(<SyncPage />, { wrapper });
    
    const chaptersTextarea = screen.getByLabelText('Chapters') as HTMLTextAreaElement;
    
    const multilineText = '[00:00:00] Introduction\n[00:05:00] Topic 1\n[00:10:00] Topic 2';
    await user.type(chaptersTextarea, multilineText);
    
    expect(chaptersTextarea.value).toBe(multilineText);
  });
});