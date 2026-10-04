export interface Dimensions { length: number; width: number; height: number }
export interface BoxDimensions extends Dimensions {thickness:number}
export interface Geometry extends BoxDimensions { faces: {id:string;label:string;x:number;y:number;width:number;height:number}[]; folds:number[][]; net_width:number;net_height:number;surface_area:number;volume:number;seam_allowance:number;bend_allowance:number;net_origin:number }
export interface Pad extends Dimensions {id:string;name:string;x:number;y:number;z:number}
export interface Design extends BoxDimensions {id:number;name:string;created_at:string;pads:Pad[]}
