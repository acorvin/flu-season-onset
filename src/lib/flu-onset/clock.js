// Shared by the page: the season's colors and its clock face.
// The archive in sepia, this season in rose, and the 2009 pandemic, which is not a usual season, in slate.
export const SEPIA = '#a8793a', ROSE = '#c06a85', SLATE = '#3f6c96';

export const NW = 52; // one point per week, early October at the top, clockwise
export const angleOf = (w) => -Math.PI / 2 + (w / NW) * Math.PI * 2;
