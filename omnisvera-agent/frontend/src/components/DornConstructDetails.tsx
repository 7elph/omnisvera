import { PlayableCharacter, CombatEffectsState, mediaUrlFromVaultPath } from '../api';
import SheetDetail from './SheetDetail';
import SpellCard from './SpellCard';
import SheetSection from './SheetSection';
const traitImages: Record<string, string> = {
  'Forma Imutável': 'zz_media/ui/icons/uploads/forma_imutavel_8ca8772cb2.jpg',
  'Mente Artificial': 'zz_media/ui/icons/uploads/mente_artificial_6180e87c7a.png',
  'Corpo Artificial': 'zz_media/ui/icons/uploads/corpo_artificial_a3e38666fb.jpg',
};
export default function DornConstructDetails({ character, combat }: { character: PlayableCharacter; combat: CombatEffectsState | null }) {
  const traits = String(character.definition.abilities?.racial || '').split(/(?<=\.)\s+/).filter(trait => ['Forma Imutável', 'Mente Artificial', 'Corpo Artificial'].includes(trait.split(':')[0]));
  return <SheetSection title="Traços de constructo">
    <section className="workspace-action-catalog"><header><span>TRAÇOS DE CONSTRUCTO</span></header>
      {traits.map((trait, index) => <SpellCard key={index} heading={<SheetDetail title={trait.split(':')[0]} description={trait} icon={mediaUrlFromVaultPath(traitImages[trait.split(':')[0]])} />} summary={<small>Passiva</small>} />)}
    </section>
  </SheetSection>;
}
