export type BindingSide = 'left' | 'right' | 'top' | 'bottom'
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
  timelinePages: 1 | 2
  timelineSwapPages: boolean
  timelineStart: number
  timelineEnd: number
  timelineColor: string
}