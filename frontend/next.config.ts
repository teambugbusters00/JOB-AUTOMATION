import type {NextConfig} from "next";

const nextConfig:NextConfig={
  poweredByHeader:false,
  reactStrictMode:true,
  async rewrites(){return [
    {source:"/api/:path*",destination:"http://127.0.0.1:8000/api/:path*"},
    {source:"/health",destination:"http://127.0.0.1:8000/health"},
    {source:"/admin",destination:"http://127.0.0.1:8000/admin"},
    {source:"/admin/:path*",destination:"http://127.0.0.1:8000/admin/:path*"},
  ]}
};
export default nextConfig;
