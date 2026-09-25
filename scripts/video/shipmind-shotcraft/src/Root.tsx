import { Composition } from 'remotion';
import { AIFL_TOTAL } from './aifl/Main';
import { ThemedFilm } from './themes/ThemedFilm';
import { ShipMindPromo } from './shipmind/Main';
import { TOTAL as SHIPMIND_TOTAL } from './shipmind/shots';

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="AiflPromo"
        component={ThemedFilm}
        defaultProps={{theme: 'ink-press'}}
        durationInFrames={AIFL_TOTAL}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="ShipMindPromo"
        component={ShipMindPromo}
        defaultProps={{bgm: true}}
        durationInFrames={SHIPMIND_TOTAL}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
