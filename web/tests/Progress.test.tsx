import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Progress from '../src/pages/Progress';
import { apiClient } from '../src/api/client';

vi.mock('../src/api/client', async () => {
  const actual = await vi.importActual<typeof import('../src/api/client')>('../src/api/client');
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
    },
  };
});

describe('Progress', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the log-entry form fields', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/api/progress/summary') {
        return Promise.resolve({
          data: { weeklyAverageCalories: 2100, goalAchievementPercent: 80, weightHistory: [] },
        });
      }
      return Promise.resolve({ data: [] });
    });

    render(
      <MemoryRouter>
        <Progress />
      </MemoryRouter>,
    );

    expect(screen.getByLabelText(/weight \(kg\)/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/calories/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log entry/i })).toBeInTheDocument();
  });

  it('shows the weekly average and goal percentage from the summary', async () => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (url === '/api/progress/summary') {
        return Promise.resolve({
          data: { weeklyAverageCalories: 2100, goalAchievementPercent: 80, weightHistory: [] },
        });
      }
      return Promise.resolve({ data: [] });
    });

    render(
      <MemoryRouter>
        <Progress />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('2100')).toBeInTheDocument();
    });
    expect(screen.getByText('80%')).toBeInTheDocument();
  });
});
