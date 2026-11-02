import Link from "next/link";

export default function NotFound() {
  return (
    <div className="max-w-xl mx-auto p-8 space-y-3">
      <h1 className="text-2xl font-bold">Page not found</h1>
      <p className="text-zinc-700">This address doesn&apos;t match anything in BrandGuard.</p>
      <Link href="/" className="underline font-medium">Go to the home page</Link>
    </div>
  );
}
