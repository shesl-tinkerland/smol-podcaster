import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import EditEpisodePage from '../page';
import { episodeApi } from '@/lib/api';
import { ProcessingStatus } from '@/types';

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useParams: () => ({ id: 'test-episode-123' }),
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock the API
jest.mock('@/lib/api', () => ({
  episodeApi: {
    get: jest.fn(),
    updateShowNotes: jest.fn()
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

describe('EditEpisodePage', () => {
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

  const mockEpisode = {
    id: 'test-episode-123',
    name: 'Test Episode',
    speakers_count: 2,
    status: ProcessingStatus.COMPLETED,
    created_at: '2024-01-01T00:00:00',
    updated_at: '2024-01-01T00:00:00',
    show_notes: [
      { text: 'Note 1', url: 'https://example1.com' },
      { text: 'Note 2', url: null }
    ]
  };

  it('displays loading state initially', () => {
    (episodeApi.get as jest.Mock).mockImplementation(() => new Promise(() => {}));

    render(<EditEpisodePage />, { wrapper });

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays episode name and show notes when loaded', async () => {
    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    // Check if show notes are rendered
    const textInputs = screen.getAllByPlaceholderText('Item text');
    const urlInputs = screen.getAllByPlaceholderText('URL (optional)');

    expect(textInputs).toHaveLength(2);
    expect(urlInputs).toHaveLength(2);
    expect(textInputs[0]).toHaveValue('Note 1');
    expect(urlInputs[0]).toHaveValue('https://example1.com');
    expect(textInputs[1]).toHaveValue('Note 2');
    expect(urlInputs[1]).toHaveValue('');
  });

  it('adds a new show note item when Add Item is clicked', async () => {
    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    const addButton = screen.getByRole('button', { name: /Add Item/i });
    await user.click(addButton);

    const textInputs = screen.getAllByPlaceholderText('Item text');
    expect(textInputs).toHaveLength(3);
  });

  it('removes a show note item when delete button is clicked', async () => {
    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: '' }); // Icon buttons
    // Filter to get only delete buttons (not the Add or other buttons)
    const deleteButton = deleteButtons[0];
    await user.click(deleteButton);

    const textInputs = screen.getAllByPlaceholderText('Item text');
    expect(textInputs).toHaveLength(1);
  });

  it('updates show note text when typed', async () => {
    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    const textInputs = screen.getAllByPlaceholderText('Item text') as HTMLInputElement[];
    await user.clear(textInputs[0]);
    await user.type(textInputs[0], 'Updated Note 1');

    expect(textInputs[0]).toHaveValue('Updated Note 1');
  });

  it('updates show note URL when typed', async () => {
    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    const urlInputs = screen.getAllByPlaceholderText('URL (optional)') as HTMLInputElement[];
    await user.clear(urlInputs[0]);
    await user.type(urlInputs[0], 'https://updated.com');

    expect(urlInputs[0]).toHaveValue('https://updated.com');
  });

  it('submits updated show notes when Save Changes is clicked', async () => {
    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);
    (episodeApi.updateShowNotes as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    const textInputs = screen.getAllByPlaceholderText('Item text') as HTMLInputElement[];
    await user.clear(textInputs[0]);
    await user.type(textInputs[0], 'Updated Note');

    const saveButton = screen.getByRole('button', { name: 'Save Changes' });
    await user.click(saveButton);

    await waitFor(() => {
      expect(episodeApi.updateShowNotes).toHaveBeenCalledWith(
        'test-episode-123',
        [
          { text: 'Updated Note', url: 'https://example1.com' },
          { text: 'Note 2', url: '' }
        ]
      );
    });
  });

  it('filters out empty show notes before submitting', async () => {
    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);
    (episodeApi.updateShowNotes as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    // Clear the second note
    const textInputs = screen.getAllByPlaceholderText('Item text') as HTMLInputElement[];
    await user.clear(textInputs[1]);

    const saveButton = screen.getByRole('button', { name: 'Save Changes' });
    await user.click(saveButton);

    await waitFor(() => {
      expect(episodeApi.updateShowNotes).toHaveBeenCalledWith(
        'test-episode-123',
        [
          { text: 'Note 1', url: 'https://example1.com' }
        ]
      );
    });
  });

  it('navigates back when Cancel is clicked', async () => {
    const mockPush = jest.fn();
    jest.spyOn(require('next/navigation'), 'useRouter').mockReturnValue({
      push: mockPush
    });

    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    const cancelButton = screen.getByRole('button', { name: 'Cancel' });
    await user.click(cancelButton);

    expect(mockPush).toHaveBeenCalledWith('/episodes');
  });

  it('navigates back when Back to Episodes is clicked', async () => {
    const mockPush = jest.fn();
    jest.spyOn(require('next/navigation'), 'useRouter').mockReturnValue({
      push: mockPush
    });

    (episodeApi.get as jest.Mock).mockResolvedValue(mockEpisode);

    render(<EditEpisodePage />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Edit Show Notes: Test Episode')).toBeInTheDocument();
    });

    const backButton = screen.getByRole('button', { name: /Back to Episodes/i });
    await user.click(backButton);

    expect(mockPush).toHaveBeenCalledWith('/episodes');
  });
});