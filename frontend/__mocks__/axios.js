const mockAxiosInstance = {
  get: jest.fn(() => Promise.resolve({ data: {} })),
  interceptors: {
    request: { use: jest.fn(), eject: jest.fn() },
    response: { use: jest.fn(), eject: jest.fn() }
  }
};

const mockAxios = {
  create: jest.fn(() => mockAxiosInstance),
  ...mockAxiosInstance
};

module.exports = mockAxios;
