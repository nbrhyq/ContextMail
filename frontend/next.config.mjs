const isGitHubPages = process.env.GITHUB_ACTIONS === "true";
const repositoryBasePath = "/ContextMail";

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: isGitHubPages ? repositoryBasePath : "",
  assetPrefix: isGitHubPages ? `${repositoryBasePath}/` : "",
  images: { unoptimized: true },
};

export default nextConfig;
