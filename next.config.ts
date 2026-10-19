import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  serverExternalPackages: [
    'genkit',
    '@genkit-ai/core',
    '@genkit-ai/googleai',
    '@opentelemetry/sdk-node',
    '@opentelemetry/instrumentation'
  ],
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'placehold.co',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'images.unsplash.com',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'picsum.photos',
        port: '',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'storage.googleapis.com',
        port: '',
        pathname: '/**',
      },
    ],
  },
  async rewrites() {
    const mlUrl = process.env.ML_API_URL || 'http://127.0.0.1:8000';
    return [
      {
        source: '/v1/:path*',
        destination: `${mlUrl}/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
