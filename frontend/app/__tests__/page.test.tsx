import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import HomePage from '../page';
import { episodeApi } from '@/lib/api';

// Mock the API
jest.mock('@/lib/api', () => ({
  episodeApi: {
    create: jest.fn()
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

describe('HomePage', () => {
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
    render(<HomePage />, { wrapper });
    expect(screen.getByText('Create Writeup')).toBeInTheDocument();
  });

  it('renders all form fields', () => {
    render(<HomePage />, { wrapper });
    
    expect(screen.getByLabelText('Audio File')).toBeInTheDocument();
    expect(screen.getByLabelText('URL')).toBeInTheDocument();
    expect(screen.getByLabelText('Number of Speakers')).toBeInTheDocument();
    expect(screen.getByLabelText('Episode Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Transcript Only')).toBeInTheDocument();
    expect(screen.getByLabelText('Generate titles and tweets')).toBeInTheDocument();
  });

  it('disables submit button when required fields are empty', () => {
    render(<HomePage />, { wrapper });
    
    const submitButton = screen.getByRole('button', { name: 'Create Artifacts' });
    expect(submitButton).toBeDisabled();
  });

  it('enables submit button when required fields are filled', async () => {
    render(<HomePage />, { wrapper });
    
    const urlInput = screen.getByLabelText('URL');
    const nameInput = screen.getByLabelText('Episode Name');
    
    await user.type(urlInput, 'https://example.com/audio.mp3');
    await user.type(nameInput, 'Test Episode');
    
    const submitButton = screen.getByRole('button', { name: 'Create Artifacts' });
    expect(submitButton).toBeEnabled();
  });

  it('submits form with URL', async () => {
    const mockEpisode = {
      id: 'test-123',
      name: 'Test Episode',
      speakers_count: 2,
      status: 'pending',
      created_at: '2024-01-01T00:00:00',
      updated_at: '2024-01-01T00:00:00'
    };

    (episodeApi.create as jest.Mock).mockResolvedValue(mockEpisode);

    render(<HomePage />, { wrapper });
    
    const urlInput = screen.getByLabelText('URL');
    const nameInput = screen.getByLabelText('Episode Name');
    const speakersInput = screen.getByLabelText('Number of Speakers');
    
    await user.type(urlInput, 'https://example.com/audio.mp3');
    await user.type(nameInput, 'Test Episode');
    await user.clear(speakersInput);
    await user.type(speakersInput, '3');
    
    const submitButton = screen.getByRole('button', { name: 'Create Artifacts' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(episodeApi.create).toHaveBeenCalledWith(expect.any(FormData));
    });
    
    const formData = (episodeApi.create as jest.Mock).mock.calls[0][0];
    expect(formData.get('url')).toBe('https://example.com/audio.mp3');
    expect(formData.get('name')).toBe('Test Episode');
    expect(formData.get('speakers_count')).toBe('3');
  });

  it('submits form with file upload', async () => {
    const mockEpisode = {
      id: 'test-123',
      name: 'Test Episode',
      speakers_count: 2,
      status: 'pending',
      created_at: '2024-01-01T00:00:00',
      updated_at: '2024-01-01T00:00:00'
    };

    (episodeApi.create as jest.Mock).mockResolvedValue(mockEpisode);

    render(<HomePage />, { wrapper });
    
    const file = new File(['audio content'], 'test.mp3', { type: 'audio/mpeg' });
    const fileInput = screen.getByLabelText('Audio File');
    const nameInput = screen.getByLabelText('Episode Name');
    
    await user.upload(fileInput, file);
    await user.type(nameInput, 'Test Episode');
    
    const submitButton = screen.getByRole('button', { name: 'Create Artifacts' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(episodeApi.create).toHaveBeenCalledWith(expect.any(FormData));
    });
    
    const formData = (episodeApi.create as jest.Mock).mock.calls[0][0];
    expect(formData.get('file')).toBe(file);
    expect(formData.get('name')).toBe('Test Episode');
  });

  it('handles checkbox inputs correctly', async () => {
    const mockEpisode = {
      id: 'test-123',
      name: 'Test Episode',
      speakers_count: 2,
      status: 'pending',
      created_at: '2024-01-01T00:00:00',
      updated_at: '2024-01-01T00:00:00'
    };

    (episodeApi.create as jest.Mock).mockResolvedValue(mockEpisode);

    render(<HomePage />, { wrapper });
    
    const transcriptOnlyCheckbox = screen.getByLabelText('Transcript Only');
    const generateExtraCheckbox = screen.getByLabelText('Generate titles and tweets');
    const urlInput = screen.getByLabelText('URL');
    const nameInput = screen.getByLabelText('Episode Name');
    
    await user.type(urlInput, 'https://example.com/audio.mp3');
    await user.type(nameInput, 'Test Episode');
    await user.click(transcriptOnlyCheckbox);
    await user.click(generateExtraCheckbox);
    
    const submitButton = screen.getByRole('button', { name: 'Create Artifacts' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(episodeApi.create).toHaveBeenCalled();
    });
    
    const formData = (episodeApi.create as jest.Mock).mock.calls[0][0];
    expect(formData.get('transcript_only')).toBe('true');
    expect(formData.get('generate_extra')).toBe('true');
  });

  it('shows success message after successful submission', async () => {
    const mockEpisode = {
      id: 'test-123',
      name: 'Test Episode',
      speakers_count: 2,
      status: 'pending',
      created_at: '2024-01-01T00:00:00',
      updated_at: '2024-01-01T00:00:00'
    };

    (episodeApi.create as jest.Mock).mockResolvedValue(mockEpisode);

    render(<HomePage />, { wrapper });
    
    const urlInput = screen.getByLabelText('URL');
    const nameInput = screen.getByLabelText('Episode Name');
    
    await user.type(urlInput, 'https://example.com/audio.mp3');
    await user.type(nameInput, 'Test Episode');
    
    const submitButton = screen.getByRole('button', { name: 'Create Artifacts' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Processing started for Test Episode')).toBeInTheDocument();
    });
  });

  it('resets form after successful submission', async () => {
    const mockEpisode = {
      id: 'test-123',
      name: 'Test Episode',
      speakers_count: 2,
      status: 'pending',
      created_at: '2024-01-01T00:00:00',
      updated_at: '2024-01-01T00:00:00'
    };

    (episodeApi.create as jest.Mock).mockResolvedValue(mockEpisode);

    render(<HomePage />, { wrapper });
    
    const urlInput = screen.getByLabelText('URL') as HTMLInputElement;
    const nameInput = screen.getByLabelText('Episode Name') as HTMLInputElement;
    
    await user.type(urlInput, 'https://example.com/audio.mp3');
    await user.type(nameInput, 'Test Episode');
    
    const submitButton = screen.getByRole('button', { name: 'Create Artifacts' });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(urlInput.value).toBe('');
      expect(nameInput.value).toBe('');
    });
  });
});