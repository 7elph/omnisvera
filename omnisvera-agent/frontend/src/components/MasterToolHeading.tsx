export default function MasterToolHeading({ icon, title, description }: {
  icon: string; title: string; description: string;
}) {
  return <><b aria-hidden="true">{icon}</b><span className="workspace-tool-copy"><strong>{title}</strong><small>{description}</small></span></>;
}
