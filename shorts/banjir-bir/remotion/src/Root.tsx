import React from "react";
import { Composition } from "remotion";

import { BeerShort, BEER_FRAMES } from "./videos/beer/Beer";
export const Root: React.FC = () => (
  <>

    <Composition id="BeerShort" component={BeerShort} durationInFrames={BEER_FRAMES} fps={30} width={1080} height={1920} />
  </>
);
