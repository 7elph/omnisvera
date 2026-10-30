import { mediaUrlFromVaultPath, WorkspaceToken } from '../api';
import SheetDetail from './SheetDetail';

export default function SkeletonReward({ token }: { token: WorkspaceToken }) {
  return <>{token.sheet?.reward_items?.map(item => <div key={item.name} className="workspace-catalog-card-heading">
    <SheetDetail title={item.name} icon={mediaUrlFromVaultPath(item.image_path)} description={item.description || item.name} />
    <small>{item.equipped ? 'Equipada por Morthak' : 'No inventário de Morthak'}</small>
  </div>)}</>;
}
