export type BindingSide = 'left' | 'right' | 'top' | 'bottom'
export type PunchSide = '长边打孔' | '短边打孔'
export type LayoutMode = 'center' | 'spread'
export type TimelineSide = 'left' | 'right'

export interface PageSettings {
  width: number
  height: number
  top: number
  right: number
  bottom: number
  left: number
  gridStep: number
  gridColor: string
  dotColor: string
  centerDotColor: string
  showPunchHoles: boolean
  holeDiameter: 4 | 5
  punchSide: PunchSide
  layout: LayoutMode
  timelineSide: TimelineSide
  timelineColor: string
}