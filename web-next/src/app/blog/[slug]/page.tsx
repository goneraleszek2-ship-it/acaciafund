export const generateStaticParams = async () => {
  return [{ slug: '2026-03-06-aml' }];
};

export default function BlogPost({ params }: { params: { slug: string } }) {
  return <div>BlogPost: {params.slug}</div>;
}
