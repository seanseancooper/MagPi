/*==========================================================================
  Filename: Cango-29v04.js
  Rev: 29
  By: Dr A.R.Collins
  Description: A graphics library for the canvas element.

  Copyright 2012-2025 A.R.Collins
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
  For more detail about the GNU General Public License see
  <https://www.gnu.org/licenses/>.
    
  Giving credit to A.R.Collins <http://www.arc.id.au> would be appreciated.
  Report bugs to tony at arc.id.au.

  Date   |Description                                                   |By
  --------------------------------------------------------------------------
  14Oct12 Rev 1.00 First release based on Cango0v43                      ARC
  29Nov12 Released as Cango2v00                                          ARC
  06May14 Released as Cango4v00                                          ARC
  14Jul14 Released as Cango-5v00                                         ARC
  09Feb15 Released as Cango-6v00                                         ARC
  20Mar15 Released as Cango-7v00                                         ARC
  21Dec15 Released as Cango-8v00                                         ARC
  28Mar17 Released as Cango-9v00                                         ARC
  10Jul17 Released as Cango-10v00                                        ARC
  22Jul17 Released as Cango-11v00                                        ARC
  15Aug17 Released as Cango-12v00                                        ARC
  02Mar18 Released as Cango-13v00                                        ARC
  12Aug19 Released as Cango-15v00 (no transform, no shapeDefs)           ARC 
  19Nov19 Released as Cango-17v00                                        ARC
  10Jul20 Released as Cango-19v00                                        ARC
  08Nov20 Released as Cango-21v00                                        ARC
  11Jun21 Released as Cango-22v00                                        ARC
  02Jul21 Released as Cango-24v00                                        ARC
  05Oct21 Released as Cango-25v00                                        ARC
  12Apr22 Released as Cango-26v00                                        ARC
  14Apr22 Renamed dragOffset to more meaningful dragPos                  ARC
  15Apr22 Run drag-n-drop handler in the Cango calling scope
          bugfix: Missing return on getStyleProperty                     ARC
  30Jun22 Swapped argument order of enableDrag                           ARC
  01Jul22 Added transformRestore                                         ARC
  11Aug22 bugfix: scale Text fontSize for zoom before measuring          ARC
  16Jan23 Tidy gridbox dimension setting with consistent names           ARC
  09Feb23 Use classes throughout                                         ARC
  13Feb23 Added eventData.cancelDrag fn, software callable drop event    ARC
  18Feb23 bugfix: savScale for lineWidthWC lost since 25v01, put it back ARC
  20Feb23 Allow scl transform property to take Array(2) as argument      ARC
  21Feb23 Added flip as a transform property                             ARC
  08Apr23 Enable zoom-n-pan to handle canvas resize                      ARC
  15Apr23 bugfix: Obj2D transform properties set twice                   ARC 
  25Apr23 Reset clipMasks after all render not each child Group render   ARC 
  12Jun23 Refactor drag-n-drop and remove grabTransformRestore           ARC
  15Jun23 Simplify currOfsTfmAry to prevent it growing                   ARC
  16Jun23 Released as Cango-27v00                                        ARC
  31Aug23 Remove canvas Path2D references to facilitate translations     ARC
  13Mar24 Use own matrix methods instead of DOMMatrix                    ARC
  21Mar24 Refactor to use matrix multiply without reversing order        ARC
  22Mar24 Released as Cango-28v00                                        ARC
  31Nar24 Restore Path2D and DOMMatrix use (28v02)                       ARC
  09Apr24 Included core PathSVG into the core Cango (28v06)              ARC
  01Jun24 Drop ImageSegment replace with Img.crop method (28v07)         ARC
  13Jun24 bugfix: PATH and SHAPE dup getting ClipMask.paint method       ARC
  06Jan25 bugfix: dropShadows ignoring Shape's iso value                 ARC
  17Jan25 Add support for down and cancel event handlers for enableClick ARC
  20Jan25 Add gc (Cango context) to Drag n Drop eventData                ARC
  22Jan25 Tidy some y scale handling for clarity
          Renamed yWC_to_isoWC to correct meaning isoWC_to_yWC           ARC
  06Feb25 Got all matrix transforms to be applied in reverse order       ARC
  08Feb25 Released as Cango-29v00                                        ARC
  19Feb25 To simplify porting, make all matrix operations function calls ARC
  21Feb25 Swap matrixMult order, apply transforms in order of insertion  ARC
  23Feb25 Update to use PathSVG-5v00 code which adds transform method    ARC
  15Apr25 bugfix: clip mask not cleared for each nested Group            ARC
  ==========================================================================*/

  "use strict";
  var Cango, PathSVG,
      Path, Shape, Img, Text, ClipMask, Group,
      LinearGradient, RadialGradient; 

(function() {
  const types = ["GRP", "PATH", "SHAPE", "IMG", "TEXT", "CLIP"];

    if (!SVGPathElement.prototype.getPathData || !SVGPathElement.prototype.setPathData) {
      // @info
      //   Polyfill for SVG getPathData() and setPathData() methods. Based on:
      //   - SVGPathSeg polyfill by Philip Rogers (MIT License)
      //     https://github.com/progers/pathseg
      //   - SVGPathNormalizer by Tadahisa Motooka (MIT License)
      //     https://github.com/motooka/SVGPathNormalizer/tree/master/src
      //   - arcToCubicCurves() by Dmitry Baranovskiy (MIT License)
      //     https://github.com/DmitryBaranovskiy/raphael/blob/v2.1.1/raphael.core.js#L1837
      // @author
      //   Jarosław Foksa
      // @source
      //   https://github.com/jarek-foksa/path-data-polyfill.js/
      // @license
      //   MIT License
      !function(){var e={Z:"Z",M:"M",L:"L",C:"C",Q:"Q",A:"A",H:"H",V:"V",S:"S",T:"T",z:"Z",m:"m",l:"l",c:"c",q:"q",a:"a",h:"h",v:"v",s:"s",t:"t"},t=function(e){this._string=e,this._currentIndex=0,this._endIndex=this._string.length,this._prevCommand=null,this._skipOptionalSpaces()},s=-1!==window.navigator.userAgent.indexOf("MSIE ")
      t.prototype={parseSegment:function(){var t=this._string[this._currentIndex],s=e[t]?e[t]:null
      if(null===s){if(null===this._prevCommand)return null
      if(s=("+"===t||"-"===t||"."===t||t>="0"&&"9">=t)&&"Z"!==this._prevCommand?"M"===this._prevCommand?"L":"m"===this._prevCommand?"l":this._prevCommand:null,null===s)return null}else this._currentIndex+=1
      this._prevCommand=s
      var r=null,a=s.toUpperCase()
      return"H"===a||"V"===a?r=[this._parseNumber()]:"M"===a||"L"===a||"T"===a?r=[this._parseNumber(),this._parseNumber()]:"S"===a||"Q"===a?r=[this._parseNumber(),this._parseNumber(),this._parseNumber(),this._parseNumber()]:"C"===a?r=[this._parseNumber(),this._parseNumber(),this._parseNumber(),this._parseNumber(),this._parseNumber(),this._parseNumber()]:"A"===a?r=[this._parseNumber(),this._parseNumber(),this._parseNumber(),this._parseArcFlag(),this._parseArcFlag(),this._parseNumber(),this._parseNumber()]:"Z"===a&&(this._skipOptionalSpaces(),r=[]),null===r||r.indexOf(null)>=0?null:{type:s,values:r}},hasMoreData:function(){return this._currentIndex<this._endIndex},peekSegmentType:function(){var t=this._string[this._currentIndex]
      return e[t]?e[t]:null},initialCommandIsMoveTo:function(){if(!this.hasMoreData())return!0
      var e=this.peekSegmentType()
      return"M"===e||"m"===e},_isCurrentSpace:function(){var e=this._string[this._currentIndex]
      return" ">=e&&(" "===e||"\n"===e||"	"===e||"\r"===e||"\f"===e)},_skipOptionalSpaces:function(){for(;this._currentIndex<this._endIndex&&this._isCurrentSpace();)this._currentIndex+=1
      return this._currentIndex<this._endIndex},_skipOptionalSpacesOrDelimiter:function(){return this._currentIndex<this._endIndex&&!this._isCurrentSpace()&&","!==this._string[this._currentIndex]?!1:(this._skipOptionalSpaces()&&this._currentIndex<this._endIndex&&","===this._string[this._currentIndex]&&(this._currentIndex+=1,this._skipOptionalSpaces()),this._currentIndex<this._endIndex)},_parseNumber:function(){var e=0,t=0,s=1,r=0,a=1,n=1,u=this._currentIndex
      if(this._skipOptionalSpaces(),this._currentIndex<this._endIndex&&"+"===this._string[this._currentIndex]?this._currentIndex+=1:this._currentIndex<this._endIndex&&"-"===this._string[this._currentIndex]&&(this._currentIndex+=1,a=-1),this._currentIndex===this._endIndex||(this._string[this._currentIndex]<"0"||this._string[this._currentIndex]>"9")&&"."!==this._string[this._currentIndex])return null
      for(var i=this._currentIndex;this._currentIndex<this._endIndex&&this._string[this._currentIndex]>="0"&&this._string[this._currentIndex]<="9";)this._currentIndex+=1
      if(this._currentIndex!==i)for(var l=this._currentIndex-1,h=1;l>=i;)t+=h*(this._string[l]-"0"),l-=1,h*=10
      if(this._currentIndex<this._endIndex&&"."===this._string[this._currentIndex]){if(this._currentIndex+=1,this._currentIndex>=this._endIndex||this._string[this._currentIndex]<"0"||this._string[this._currentIndex]>"9")return null
      for(;this._currentIndex<this._endIndex&&this._string[this._currentIndex]>="0"&&this._string[this._currentIndex]<="9";)s*=10,r+=(this._string.charAt(this._currentIndex)-"0")/s,this._currentIndex+=1}if(this._currentIndex!==u&&this._currentIndex+1<this._endIndex&&("e"===this._string[this._currentIndex]||"E"===this._string[this._currentIndex])&&"x"!==this._string[this._currentIndex+1]&&"m"!==this._string[this._currentIndex+1]){if(this._currentIndex+=1,"+"===this._string[this._currentIndex]?this._currentIndex+=1:"-"===this._string[this._currentIndex]&&(this._currentIndex+=1,n=-1),this._currentIndex>=this._endIndex||this._string[this._currentIndex]<"0"||this._string[this._currentIndex]>"9")return null
      for(;this._currentIndex<this._endIndex&&this._string[this._currentIndex]>="0"&&this._string[this._currentIndex]<="9";)e*=10,e+=this._string[this._currentIndex]-"0",this._currentIndex+=1}var v=t+r
      return v*=a,e&&(v*=Math.pow(10,n*e)),u===this._currentIndex?null:(this._skipOptionalSpacesOrDelimiter(),v)},_parseArcFlag:function(){if(this._currentIndex>=this._endIndex)return null
      var e=null,t=this._string[this._currentIndex]
      if(this._currentIndex+=1,"0"===t)e=0
      else{if("1"!==t)return null
      e=1}return this._skipOptionalSpacesOrDelimiter(),e}}
      var r=function(e){if(!e||0===e.length)return[]
      var s=new t(e),r=[]
      if(s.initialCommandIsMoveTo())for(;s.hasMoreData();){var a=s.parseSegment()
      if(null===a)break
      r.push(a)}return r},a=SVGPathElement.prototype.setAttribute,n=SVGPathElement.prototype.removeAttribute,u=window.Symbol?Symbol():"__cachedPathData",i=window.Symbol?Symbol():"__cachedNormalizedPathData",l=function(e,t,s,r,a,n,u,i,h,v){var p,_,c,o,d=function(e){return Math.PI*e/180},y=function(e,t,s){var r=e*Math.cos(s)-t*Math.sin(s),a=e*Math.sin(s)+t*Math.cos(s)
      return{x:r,y:a}},x=d(u),f=[]
      if(v)p=v[0],_=v[1],c=v[2],o=v[3]
      else{var I=y(e,t,-x)
      e=I.x,t=I.y
      var m=y(s,r,-x)
      s=m.x,r=m.y
      var g=(e-s)/2,b=(t-r)/2,M=g*g/(a*a)+b*b/(n*n)
      M>1&&(M=Math.sqrt(M),a=M*a,n=M*n)
      var S
      S=i===h?-1:1
      var V=a*a,A=n*n,C=V*A-V*b*b-A*g*g,P=V*b*b+A*g*g,N=S*Math.sqrt(Math.abs(C/P))
      c=N*a*b/n+(e+s)/2,o=N*-n*g/a+(t+r)/2,p=Math.asin(parseFloat(((t-o)/n).toFixed(9))),_=Math.asin(parseFloat(((r-o)/n).toFixed(9))),c>e&&(p=Math.PI-p),c>s&&(_=Math.PI-_),0>p&&(p=2*Math.PI+p),0>_&&(_=2*Math.PI+_),h&&p>_&&(p-=2*Math.PI),!h&&_>p&&(_-=2*Math.PI)}var E=_-p
      if(Math.abs(E)>120*Math.PI/180){var D=_,O=s,L=r
      _=h&&_>p?p+120*Math.PI/180*1:p+120*Math.PI/180*-1,s=c+a*Math.cos(_),r=o+n*Math.sin(_),f=l(s,r,O,L,a,n,u,0,h,[_,D,c,o])}E=_-p
      var k=Math.cos(p),G=Math.sin(p),T=Math.cos(_),Z=Math.sin(_),w=Math.tan(E/4),H=4/3*a*w,Q=4/3*n*w,z=[e,t],F=[e+H*G,t-Q*k],q=[s+H*Z,r-Q*T],j=[s,r]
      if(F[0]=2*z[0]-F[0],F[1]=2*z[1]-F[1],v)return[F,q,j].concat(f)
      f=[F,q,j].concat(f)
      for(var R=[],U=0;U<f.length;U+=3){var a=y(f[U][0],f[U][1],x),n=y(f[U+1][0],f[U+1][1],x),B=y(f[U+2][0],f[U+2][1],x)
      R.push([a.x,a.y,n.x,n.y,B.x,B.y])}return R},h=function(e){return e.map(function(e){return{type:e.type,values:Array.prototype.slice.call(e.values)}})},v=function(e){var t=[],s=null,r=null,a=null,n=null
      return e.forEach(function(e){var u=e.type
      if("M"===u){var i=e.values[0],l=e.values[1]
      t.push({type:"M",values:[i,l]}),a=i,n=l,s=i,r=l}else if("m"===u){var i=s+e.values[0],l=r+e.values[1]
      t.push({type:"M",values:[i,l]}),a=i,n=l,s=i,r=l}else if("L"===u){var i=e.values[0],l=e.values[1]
      t.push({type:"L",values:[i,l]}),s=i,r=l}else if("l"===u){var i=s+e.values[0],l=r+e.values[1]
      t.push({type:"L",values:[i,l]}),s=i,r=l}else if("C"===u){var h=e.values[0],v=e.values[1],p=e.values[2],_=e.values[3],i=e.values[4],l=e.values[5]
      t.push({type:"C",values:[h,v,p,_,i,l]}),s=i,r=l}else if("c"===u){var h=s+e.values[0],v=r+e.values[1],p=s+e.values[2],_=r+e.values[3],i=s+e.values[4],l=r+e.values[5]
      t.push({type:"C",values:[h,v,p,_,i,l]}),s=i,r=l}else if("Q"===u){var h=e.values[0],v=e.values[1],i=e.values[2],l=e.values[3]
      t.push({type:"Q",values:[h,v,i,l]}),s=i,r=l}else if("q"===u){var h=s+e.values[0],v=r+e.values[1],i=s+e.values[2],l=r+e.values[3]
      t.push({type:"Q",values:[h,v,i,l]}),s=i,r=l}else if("A"===u){var i=e.values[5],l=e.values[6]
      t.push({type:"A",values:[e.values[0],e.values[1],e.values[2],e.values[3],e.values[4],i,l]}),s=i,r=l}else if("a"===u){var i=s+e.values[5],l=r+e.values[6]
      t.push({type:"A",values:[e.values[0],e.values[1],e.values[2],e.values[3],e.values[4],i,l]}),s=i,r=l}else if("H"===u){var i=e.values[0]
      t.push({type:"H",values:[i]}),s=i}else if("h"===u){var i=s+e.values[0]
      t.push({type:"H",values:[i]}),s=i}else if("V"===u){var l=e.values[0]
      t.push({type:"V",values:[l]}),r=l}else if("v"===u){var l=r+e.values[0]
      t.push({type:"V",values:[l]}),r=l}else if("S"===u){var p=e.values[0],_=e.values[1],i=e.values[2],l=e.values[3]
      t.push({type:"S",values:[p,_,i,l]}),s=i,r=l}else if("s"===u){var p=s+e.values[0],_=r+e.values[1],i=s+e.values[2],l=r+e.values[3]
      t.push({type:"S",values:[p,_,i,l]}),s=i,r=l}else if("T"===u){var i=e.values[0],l=e.values[1]
      t.push({type:"T",values:[i,l]}),s=i,r=l}else if("t"===u){var i=s+e.values[0],l=r+e.values[1]
      t.push({type:"T",values:[i,l]}),s=i,r=l}else("Z"===u||"z"===u)&&(t.push({type:"Z",values:[]}),s=a,r=n)}),t},p=function(e){var t=[],s=null,r=null,a=null,n=null,u=null,i=null,h=null
      return e.forEach(function(e){if("M"===e.type){var v=e.values[0],p=e.values[1]
      t.push({type:"M",values:[v,p]}),i=v,h=p,n=v,u=p}else if("C"===e.type){var _=e.values[0],c=e.values[1],o=e.values[2],d=e.values[3],v=e.values[4],p=e.values[5]
      t.push({type:"C",values:[_,c,o,d,v,p]}),r=o,a=d,n=v,u=p}else if("L"===e.type){var v=e.values[0],p=e.values[1]
      t.push({type:"L",values:[v,p]}),n=v,u=p}else if("H"===e.type){var v=e.values[0]
      t.push({type:"L",values:[v,u]}),n=v}else if("V"===e.type){var p=e.values[0]
      t.push({type:"L",values:[n,p]}),u=p}else if("S"===e.type){var y,x,o=e.values[0],d=e.values[1],v=e.values[2],p=e.values[3]
      "C"===s||"S"===s?(y=n+(n-r),x=u+(u-a)):(y=n,x=u),t.push({type:"C",values:[y,x,o,d,v,p]}),r=o,a=d,n=v,u=p}else if("T"===e.type){var _,c,v=e.values[0],p=e.values[1]
      "Q"===s||"T"===s?(_=n+(n-r),c=u+(u-a)):(_=n,c=u)
      var y=n+2*(_-n)/3,x=u+2*(c-u)/3,f=v+2*(_-v)/3,I=p+2*(c-p)/3
      t.push({type:"C",values:[y,x,f,I,v,p]}),r=_,a=c,n=v,u=p}else if("Q"===e.type){var _=e.values[0],c=e.values[1],v=e.values[2],p=e.values[3],y=n+2*(_-n)/3,x=u+2*(c-u)/3,f=v+2*(_-v)/3,I=p+2*(c-p)/3
      t.push({type:"C",values:[y,x,f,I,v,p]}),r=_,a=c,n=v,u=p}else if("A"===e.type){var m=Math.abs(e.values[0]),g=Math.abs(e.values[1]),b=e.values[2],M=e.values[3],S=e.values[4],v=e.values[5],p=e.values[6]
      if(0===m||0===g)t.push({type:"C",values:[n,u,v,p,v,p]}),n=v,u=p
      else if(n!==v||u!==p){var V=l(n,u,v,p,m,g,b,M,S)
      V.forEach(function(e){t.push({type:"C",values:e})}),n=v,u=p}}else"Z"===e.type&&(t.push(e),n=i,u=h)
      s=e.type}),t}
      SVGPathElement.prototype.setAttribute=function(e,t){"d"===e&&(this[u]=null,this[i]=null),a.call(this,e,t)},SVGPathElement.prototype.removeAttribute=function(e,t){"d"===e&&(this[u]=null,this[i]=null),n.call(this,e)},SVGPathElement.prototype.getPathData=function(e){if(e&&e.normalize){if(this[i])return h(this[i])
      var t
      this[u]?t=h(this[u]):(t=r(this.getAttribute("d")||""),this[u]=h(t))
      var s=p(v(t))
      return this[i]=h(s),s}if(this[u])return h(this[u])
      var t=r(this.getAttribute("d")||"")
      return this[u]=h(t),t},SVGPathElement.prototype.setPathData=function(e){if(0===e.length)s?this.setAttribute("d",""):this.removeAttribute("d")
      else{for(var t="",r=0,a=e.length;a>r;r+=1){var n=e[r]
      r>0&&(t+=" "),t+=n.type,n.values&&n.values.length>0&&(t+=" "+n.values.join(" "))}this.setAttribute("d",t)}},SVGRectElement.prototype.getPathData=function(e){var t=this.x.baseVal.value,s=this.y.baseVal.value,r=this.width.baseVal.value,a=this.height.baseVal.value,n=this.hasAttribute("rx")?this.rx.baseVal.value:this.ry.baseVal.value,u=this.hasAttribute("ry")?this.ry.baseVal.value:this.rx.baseVal.value
      n>r/2&&(n=r/2),u>a/2&&(u=a/2)
      var i=[{type:"M",values:[t+n,s]},{type:"H",values:[t+r-n]},{type:"A",values:[n,u,0,0,1,t+r,s+u]},{type:"V",values:[s+a-u]},{type:"A",values:[n,u,0,0,1,t+r-n,s+a]},{type:"H",values:[t+n]},{type:"A",values:[n,u,0,0,1,t,s+a-u]},{type:"V",values:[s+u]},{type:"A",values:[n,u,0,0,1,t+n,s]},{type:"Z",values:[]}]
      return i=i.filter(function(e){return"A"!==e.type||0!==e.values[0]&&0!==e.values[1]?!0:!1}),e&&e.normalize===!0&&(i=p(i)),i},SVGCircleElement.prototype.getPathData=function(e){var t=this.cx.baseVal.value,s=this.cy.baseVal.value,r=this.r.baseVal.value,a=[{type:"M",values:[t+r,s]},{type:"A",values:[r,r,0,0,1,t,s+r]},{type:"A",values:[r,r,0,0,1,t-r,s]},{type:"A",values:[r,r,0,0,1,t,s-r]},{type:"A",values:[r,r,0,0,1,t+r,s]},{type:"Z",values:[]}]
      return e&&e.normalize===!0&&(a=p(a)),a},SVGEllipseElement.prototype.getPathData=function(e){var t=this.cx.baseVal.value,s=this.cy.baseVal.value,r=this.rx.baseVal.value,a=this.ry.baseVal.value,n=[{type:"M",values:[t+r,s]},{type:"A",values:[r,a,0,0,1,t,s+a]},{type:"A",values:[r,a,0,0,1,t-r,s]},{type:"A",values:[r,a,0,0,1,t,s-a]},{type:"A",values:[r,a,0,0,1,t+r,s]},{type:"Z",values:[]}]
      return e&&e.normalize===!0&&(n=p(n)),n},SVGLineElement.prototype.getPathData=function(){return[{type:"M",values:[this.x1.baseVal.value,this.y1.baseVal.value]},{type:"L",values:[this.x2.baseVal.value,this.y2.baseVal.value]}]},SVGPolylineElement.prototype.getPathData=function(){for(var e=[],t=0;t<this.points.numberOfItems;t+=1){var s=this.points.getItem(t)
      e.push({type:0===t?"M":"L",values:[s.x,s.y]})}return e},SVGPolygonElement.prototype.getPathData=function(){for(var e=[],t=0;t<this.points.numberOfItems;t+=1){var s=this.points.getItem(t)
      e.push({type:0===t?"M":"L",values:[s.x,s.y]})}return e.push({type:"Z",values:[]}),e}}()
    }
  
    PathSVG = class extends Array
    {
      constructor (d) {
        function toSegs(pathStr)
        {
          const svgPathElem = document.createElementNS("http://www.w3.org/2000/svg", "path");
          svgPathElem.setAttribute("d", pathStr);
          const cmds2D = svgPathElem.getPathData({normalize: true}); // returns segments converted to lines and Bezier curves 
          if (cmds2D.length < 1) {
            console.error("Invalid SVG data", pathStr);
            return [];
          }
      
          return cmds2D; // returns segments converted to lines and Bezier curves 
        }
  
        if (!d || d.length === 0)
        {
          super();
        }
        else if (typeof d === 'string')
        {
          const pathStr = d.replace(/\,/g, " ");
          const svgData = toSegs(pathStr);  
          super(...svgData);
        }
        else if (Array.isArray(d))
        {
          // check typed Array views etc, convert to real Array
          if (ArrayBuffer.isView(d))    
          {
            d = Array.from(d);  
          }
          let pathStr = "";
          if (typeof(d[0]) === "number")  // its an Array of numbers
          {
            pathStr = "M "+d.join(" ");  // insert 'M' command so its valid SVG
          }
          else
          {
            pathStr = d.join(" "); 
          }
          const svgData = toSegs(pathStr);
          super(...svgData);
        }
        else
        {
          console.warn("Type Error: PathSVG constructor argument 1");
          super();   // return an empty array
        }
        this.track = null;
      } /*  constructor */
  
      dup() {
        const newPathSegs = [];
        this.forEach((seg)=>{
          newPathSegs.push(seg.type, ...seg.values);
        });
  
        return new PathSVG(newPathSegs);
      }
  
      toString(sigFigs=4) {
        let str = "";
        this.forEach((seg)=>{
          str = str.concat(seg.type);
          for (let i=0; i<seg.values.length; i+=2)
          {
            str = str.concat(seg.values[i].toPrecision(sigFigs) +","+ seg.values[i+1].toPrecision(sigFigs)+" ");
          }
        });
        return str.trim();
      }
  
      toArray() {
        const ary = [];
        this.forEach((seg)=>{
          ary.push(seg.type);
          for (let i=0; i<seg.values.length; i++)
          {
            ary.push(seg.values[i]);
          }
        });
        return ary;
      }
  
      translate(x=0, y=0) {
        const newPath = this.dup();
  
        newPath.forEach((seg)=>{
          for (let j=0; j<seg.values.length; j+=2)   // step through the coord pairs
          {
            seg.values[j] += x;
            seg.values[j+1] += y;
          }
        });
  
        return newPath;
      }
  
      scale(xScl, yScl) {
        const newPath = this.dup();
        const sx = xScl || 0.001,
              sy = yScl || sx;
  
        newPath.forEach((seg)=>{
          for (let j=0; j<seg.values.length; j+=2)   // step through the coord pairs
          {
            seg.values[j] *= sx;
            seg.values[j+1] *= sy;
          }
        });
  
        return newPath;
      }
  
      rotate(degs) {
        const newPath = this.dup();
        const angle = -degs || 0,    // formula is for +v3 CCW (SVG is +ve CW)
              toRad = Math.PI/180.0,
              s	= Math.sin(angle*toRad),
              c	= Math.cos(angle*toRad);
  
              newPath.forEach((seg)=>{
          for (let j=0; j<seg.values.length; j+=2)   // step through the coord pairs
          {
            let orgX = seg.values[j];
            let orgY = seg.values[j+1];
            seg.values[j] = orgX*c + orgY*s;
            seg.values[j+1] = -orgX*s + orgY*c;
          }
        });
  
        return newPath;
      }
  
      skew(hDegs, vDegs) {
        const newPath = this.dup();
        const ha = hDegs || 0,
              va = vDegs || 0,
              toRad = Math.PI/180.0,
              htn	= Math.tan(-ha*toRad),
              vtn	= Math.tan(va*toRad);
  
              newPath.forEach((seg)=>{
          for (let j=0; j<seg.values.length; j+=2)   // step through the coord pairs
          {
            let orgX = seg.values[j];
            let orgY = seg.values[j+1];
            seg.values[j] = orgX + orgY*htn;
            seg.values[j+1] = orgX*vtn + orgY;
          }
        });
  
        return newPath;
      }
  
      transform(M) {
        const newPath = this.dup();
        let a = 1,
            b = 0,
            c = 0,
            d = 1,
            e = 0,
            f = 0;
        if ('a' in M && 'b' in M && 'c' in M && 'd' in M && 'e' in M && 'fa' in M)
        {
          a = M.a,
          b = M.b,
          c = M.b,
          d = M.b,
          e = M.b,
          f = M.b;
        }
        else if (Array.isArray(M) && Array.isArray(M[0]) && Array.isArray(M[1]) && Array.isArray(M[2]))
        {
          a = M[0][0],
          b = M[1][0],
          c = M[0][1],
          d = M[1][1],
          e = M[0][2],
          f = M[1][2];
        } 
        else
        {
          console.warn("PathSVG.transform: invalid matrix");
          return 
        }
  
        newPath.forEach((seg)=>{
          for (let j=0; j<seg.values.length; j+=2)   // step through the coord pairs
          {
            const px = seg.values[j];
            const py = seg.values[j+1];
            seg.values[j] = px*a + py*c + e;
            seg.values[j+1] = px*b + py*d + f;
          }
        });
  
        return newPath;
      }
  
      appendPath(extensionData) {
        let extAry = [];
        let orgAry = [];
        if (!extensionData instanceof PathSVG)
        {
          console.warn("Type Error: PathSVG.appendPath argument 1");
          return;
        }
        extensionData.forEach((seg)=>{
          extAry.push(seg.type, ...seg.values);
        });
        this.forEach((seg)=>{
          orgAry.push(seg.type, ...seg.values);
        });
        // concatenate the segments
        const newPathSegs = orgAry.concat(extAry);
  
        return new PathSVG(newPathSegs);
      }
  
      joinPath(extensionData) {
        const org = this.dup();   // don't damage the original
        const newPathSegs = [];
        let extSegs;
        if (!extensionData instanceof PathSVG)
        {
          console.warn("Type Error: PathSVG.joinPath argument 1");
          return;
        }
        extSegs = extensionData;
        if (org.length == 0)  // just add the extra including the "M" command
        {
          extSegs.forEach((seg)=>{
            newPathSegs.push(seg.type, ...seg.values);
          });
        }
        else // this has length
        {
          if (org[org.length-1].type == "Z")  // closed path
          {
            org.length = org.length-1;   // delete the 'closePath'
          }
          // start with the org segs
          org.forEach((seg)=>{
            newPathSegs.push(seg.type, ...seg.values);
          });
          // now tack on the extra commands skipping the initial "M" segment
          for (let j=1; j<extSegs.length; j++)
          {
            newPathSegs.push(extSegs[j].type, ...extSegs[j].values);
          }
        }
  
        return new PathSVG(newPathSegs);
      }
  
      revWinding() {
        // reverse the direction of drawing around a path
        let cmds = this.dup(),
            zCmd = null,
            k, len,
            dCmd;
        const newPathSegs = [];  
        const newPathData = [];  
  
        function revPairs(ary)
        {
          // return a single array of x,y coords made by taking array of [x,y] arrays and reversing the order
          // eg. [1,2, 3,4, 5,6] returns [5,6, 3,4, 1,2]
          const opAry = [];
  
          for (let i=ary.length; i>0; i-=2)
          {
            opAry.push(ary[i-2], ary[i-1]);
          }
          return opAry;
        }
  
        if (cmds[cmds.length-1].type === "Z")
        {
          zCmd = cmds[cmds.length-1];
          cmds.length = cmds.length-1;     // leave off 'Z' cmd segment
        }
        // now step back along the path
        k = cmds.length-1;     // k points at the last segment in the path
        len = cmds[k].values.length;  // length of last seg coords array
        dCmd = {type:"M", values:[cmds[k].values[len-2], cmds[k].values[len-1]]};   // make a 'M' command from final coord pair
        newPathSegs.push(dCmd);         // make this the first command of the output
        cmds[k].values = cmds[k].values.slice(0,-2);  // last coord pair (we've used them)
        while (k>0)
        {
          dCmd = {type:cmds[k].type, values:revPairs(cmds[k].values)};  
          len = cmds[k-1].values.length;     // needed to find the last coord pair of the next segment back
          dCmd.values.push(cmds[k-1].values[len-2], cmds[k-1].values[len-1]); // add the last point of next cmd
          newPathSegs.push(dCmd); 
          // shove it out
          cmds[k-1].values = cmds[k-1].values.slice(0,-2);  // we've used the last point so slice it off
          k -= 1;
        }
        // add the 'z' if it was a closed path
        if (zCmd)
        {
          newPathSegs.push(zCmd);
        }
        newPathSegs.forEach((seg)=>{
          newPathData.push(seg.type, ...seg.values);
        });
  
        return new PathSVG(newPathData);
      }
      
      getPathLength() {
        const trk = new Track(this);    // this.toTrack();
        return trk.totalLength;
      }
  
      getPointAtLength(distWC) { // distance in world coords
        if (this.track === null)
        {
          this.track = new Track(this);
        }
        return this.track.trkDistToPos(distWC) 
      }
  
      getTotalLength() {
        if (this.track === null)
        {
          this.track = new Track(this);
        }
        return this.track.totalLength; 
      }
    }
  
    // ========== Static methods =============
  
    PathSVG.circle = function(d=1){
      return new PathSVG(["m", -0.5*d,0,
              "c", 0,-0.27614*d, 0.22386*d,-0.5*d, 0.5*d,-0.5*d,
              "c", 0.27614*d,0, 0.5*d,0.22386*d, 0.5*d,0.5*d,
              "c", 0,0.27614*d, -0.22386*d,0.5*d, -0.5*d,0.5*d,
              "c", -0.27614*d,0, -0.5*d,-0.22386*d, -0.5*d,-0.5*d, "z"]);
    };
  
    PathSVG.arc = function(size, begDegs, endDegs, anticlockwise){
      begDegs = begDegs % 360;
      endDegs = endDegs % 360;
      if (begDegs<0) begDegs += 360;
      if (endDegs<0) endDegs += 360;
      let ccw = (anticlockwise)? 1: 0;
      let swp = (ccw)? 0: 1;
      let lrg = (Math.abs(endDegs-begDegs)>180)? 1: 0;
      if (begDegs > endDegs) lrg = 1-lrg;
      if (ccw) lrg = 1-lrg;
  
      const secSrt = Math.PI*begDegs/180;
      const secEnd = Math.PI*endDegs/180;
  
      return new PathSVG(["M", size*Math.cos(secSrt), size*Math.sin(secSrt),
              "A", size, size, 0, lrg, swp, size*Math.cos(secEnd), size*Math.sin(secEnd)]);
    };
  
    PathSVG.ellipticalArc = function(radiusX, radiusY, startAngle=0, endAngle=180, counterClockwise) { // angles in degs
      const sAng = Math.PI*startAngle/180;
      const eAng = Math.PI*endAngle/180;
      let srtAng = sAng % (2*Math.PI);
      let endAng = eAng % (2*Math.PI);
      if (srtAng === endAng) {
        //circle time! subtract some of the angle so svg is happy (svg elliptical arc can't draw a full circle)
        endAng = ((endAng + 2*Math.PI) - 0.001 * (counterClockwise ? -1 : 1)) % (2*Math.PI);
      }
      const endX = radiusX*Math.cos(endAng),
            endY = radiusY*Math.sin(endAng),
            startX = radiusX*Math.cos(srtAng),
            startY = radiusY*Math.sin(srtAng),
            sweepFlag = counterClockwise ? 0 : 1;
      let largeArcFlag = 0;
      let diff = endAng-srtAng;
      // https://github.com/gliffy/canvas2svg/issues/4
      if (diff < 0) 
      {
        diff += 2*Math.PI;
      }
      if (counterClockwise) 
      {
        largeArcFlag = diff > Math.PI ? 0 : 1;
      } 
      else 
      {
        largeArcFlag = diff > Math.PI ? 1 : 0;
      }
  
      return new PathSVG(["M", startX, startY, "A", radiusX, radiusY, 0, largeArcFlag, sweepFlag, endX, endY]);
    }; 
  
    PathSVG.ellipse = function(width, height) {
      const w = width || 1,
            h = height || w;
  
      return new PathSVG(["m", -0.5*w,0,
              "c", 0,-0.27614*h, 0.22386*w,-0.5*h, 0.5*w,-0.5*h,
              "c", 0.27614*w,0, 0.5*w,0.22386*h, 0.5*w,0.5*h,
              "c", 0,0.27614*h, -0.22386*w,0.5*h, -0.5*w,0.5*h,
              "c", -0.27614*w,0, -0.5*w,-0.22386*h, -0.5*w,-0.5*h, "z"]);
    };
  
    PathSVG.square = function(w=1){
      return new PathSVG(["m", 0.5*w, -0.5*w, "l", 0, w, -w, 0, 0, -w, "z"]);
    };
  
    PathSVG.rectangle = function(w=2, h=1, rad=0){
      if (rad > 0)
      {
        const r = Math.min(w/2, h/2, rad);
        return new PathSVG(["m", -w/2+r,-h/2, "l",w-2*r,0, "a",r,r,0,0,1,r,r, "l",0,h-2*r,
                            "a",r,r,0,0,1,-r,r, "l",-w+2*r,0, "a",r,r,0,0,1,-r,-r, "l",0,-h+2*r,
                            "a",r,r,0,0,1,r,-r, "z"]);
      }
      return new PathSVG(["m",-w/2,-h/2, "l",w,0, 0,h, -w,0, "z"]);
    };
  
    PathSVG.triangle = function(s=1){
      return new PathSVG(["m", 0.5*s, -0.289*s, "l", -0.5*s, 0.866*s, -0.5*s, -0.866*s, "z"]);
    };
  
    PathSVG.cross = function(width=1, height){
      const w = width,
            h = height || w;
      
      return new PathSVG(["m", -0.5*w, 0, "l", w, 0, "m", -0.5*w, -0.5*h, "l", 0, h]);
    };
  
    PathSVG.ex = function(d=1){
      return new PathSVG(["m", -0.3535*d,-0.3535*d, "l",0.707*d,0.707*d,
                          "m",-0.707*d,0, "l",0.707*d,-0.707*d]);
    }; 
  
    PathSVG.arcTo = function(x0, y0, x1, y1, x2, y2, radius) {
      // Negative values for radius must cause the implementation to throw an IndexSizeError exception.
      if (!radius || radius < 0) 
      {
        console.warn("Range Error: PathSVG.arcTo bad radius");
        return ["M", x0, y0, "L", x1, y1, x2, y2];
      }
      if (((x0 === x1) && (y0 === y1))  || ((x1 === x2) && (y1 === y2))) 
      {
        console.warn("Range Error: PathSVG.arcTo parameters not independent");
        return ["M", x0, y0, "L", x1, y1, x2, y2];
      }
      const tolerance = Math.abs(Math.max(x0,x1,x2,y0,y1,y2)) * 0.000001;  
      if (Math.abs((x1 - x0)*(y2 - y0) - (x2 - x0)*(y1 - y0)) < tolerance)
      {
        console.warn("Range Error: PathSVG.arcTo parameters are collinear");
        return ["M", x0, y0, "L", x2, y2];
      }  
  
      const BA = {x:x0-x1, y:y0-y1},   // vector from B (x1,y1) to A (x0,y0)
            BC = {x:x2-x1, y:y2-y1},   // vector from B to C (x2,y2)
            // BA x BC (cross product) is normal is in z direction = 'nz' 
            nz = BA.x*BC.y - BA.y*BC.x;
      const clockwise = (nz>0)? 0: 1;      // 1=clockwise, 0=anticlockwise
      
      // ref: https://math.stackexchange.com/questions/797828/
      // TITLE = Calculate center of circle tangent to two lines in space
      // AUTHOR = g.kov (https://math.stackexchange.com/users/122782/g-kov)
  
      // side lengths 
      let a = Math.sqrt((x2-x1)*(x2-x1) + (y2-y1)*(y2-y1));
      let b = Math.sqrt((x0-x2)*(x0-x2) + (y0-y2)*(y0-y2));
      let c = Math.sqrt((x1-x0)*(x1-x0) + (y1-y0)*(y1-y0));
  
      // I = incenter 
      const I = {x:(a*x0 + b*x1 + c*x2)/(a + b + c),
                  y:(a*y0 + b*y1 + c*y2)/(a + b + c)};
  
      // tangential points of the incircle are:
      const At = {x:0.5*(x1+x2) + (b-c)*(x1-x2)/(2*a), y:0.5*(y1+y2) + (b-c)*(y1-y2)/(2*a)};
      const Bt = {x:0.5*(x0+x2) + (a-c)*(x0-x2)/(2*b), y:0.5*(y0+y2) + (a-c)*(y0-y2)/(2*b)};
      const Ct = {x:0.5*(x0+x1) + (a-b)*(x0-x1)/(2*c), y:0.5*(y0+y1) + (a-b)*(y0-y1)/(2*c)};
      const r1 = Math.sqrt((At.x-I.x)*(At.x-I.x) + (At.y-I.y)*(At.y-I.y));
  
      // arcTo at intersection ABC
      // find tangent points radius 'radius' on AB and BC
      const k = radius/r1;
      const tc = {x:x1 + k*(Ct.x-x1), y:y1 + k*(Ct.y-y1)};
      const ta = {x:x1 + k*(At.x-x1), y:y1 + k*(At.y-y1)}; 
  
      return new PathSVG(["M", x0, y0, "L", tc.x, tc.y, "A", radius, radius, 0, 0, clockwise, ta.x, ta.y, "L", x2, y2]);
    };
  
    PathSVG.splineFit = function(pts, ptsY) {
      function BuildSpline(x, y) 
      {
        // ref: GitHub skhokhlov/cubic-spline.js
        
        const splines = [];
        const n = x.length;
        for (let i = 0; i<n; i++)
        {
          splines[i] = {a:y[i],b:null,c:null,d:null,x:x[i]};
        }
        splines[0].c = 0;
        splines[n-1].c = 0;
  
        // Solution of SLAE with respect to the coefficients of splines c [i] by the sweep method for tridiagonal matrices
        // Calculation of sweep factors - forward sweep method
        var alpha = new Array(n - 1).fill(0);
        var beta  = new Array(n - 1).fill(0);
        for (let i = 1; i < n - 1; ++i) 
        {
          var hi  = x[i] - x[i - 1];
          var hi1 = x[i + 1] - x[i];
          var A = hi;
          var C = 2.0 * (hi + hi1);
          var B = hi1;
          var F = 6.0 * ((y[i + 1] - y[i]) / hi1 - (y[i] - y[i - 1]) / hi);
          var z = (A * alpha[i - 1] + C);
          alpha[i] = -B / z;
          beta[i] = (F - A * beta[i - 1]) / z;
        }
  
        // Finding a Solution - Reversing the Sweep Method
        for (let i = n - 2; i > 0; --i) {
          splines[i].c = alpha[i] * splines[i + 1].c + beta[i];
        }
  
        // Using the known coefficients c [i], we find the values ​​b [i] and d [i]
        for (let i = n - 1; i > 0; --i)
        {
          var hi = x[i] - x[i - 1];
          splines[i].d = (splines[i].c - splines[i - 1].c) / hi;
          splines[i].b = hi * (2.0 * splines[i].c + splines[i - 1].c) / 6.0 + (y[i] - y[i - 1]) / hi;
        }
  
        return splines;  // array of objects [{a:, b:, c:, d:, x:}, {a:, b:, c:, d:, x:}, ... ] 
      }
  
      function splineToBezier2(splines)
      {
        function toBezierCPs(p1x, p1y, mx, my, nx, ny, p2x, p2y)
        {
          const c1x = -5*p1x/6 + 3*mx - 3*nx/2 + p2x/3;
          const c1y = -5*p1y/6 + 3*my - 3*ny/2 + p2y/3;
          const c2x = p1x/3 - 3*mx/2 + 3*nx - 5*p2x/6;
          const c2y = p1y/3 - 3*my/2 + 3*ny - 5*p2y/6;
  
          return " C"+c1x+","+c1y+" "+c2x+","+c2y+","+p2x+","+p2y;
        }
  
        if (!Array.isArray(splines) || !splines.length)
        {
          console.warn("splineToBezier: bad spine array");
          return ""; 
        }
  
        const n = splines.length;
        let currS = splines[0];   // spline 0 just holds the start point (no spline)
        let bez = "M"+currS.x+","+currS.a;  // move to the start point
  
        for(let i=1; i<n; i++)
        {
          let prevS = currS;
          currS = splines[i];
          let mx = prevS.x + (currS.x - prevS.x)/3;    // x coord of first point on curve 1/3 way along
          let dx = mx - currS.x;  // fractional distance from end
          // We calculate the value of the spline at a given point according to Horner's scheme 
          let my = currS.a + (currS.b + (currS.c / 2.0 + currS.d * dx / 6.0) * dx) * dx;
          let nx = prevS.x + 2*(currS.x - prevS.x)/3;    // x coord of first point on curve 1/3 way along
          dx = nx - currS.x;  // fractional distance from end
          // We calculate the value of the spline at a given point according to Horner's scheme 
          let ny = currS.a + (currS.b + (currS.c / 2.0 + currS.d * dx / 6.0) * dx) * dx;
          let bezStr = toBezierCPs(prevS.x, prevS.a, mx, my, nx, ny, currS.x, currS.a);
          bez = bez.concat(bezStr);
        }
        
        return bez;
      }
  
      let splns;
      if (arguments.length === 2)
      {
        if (Array.isArray(ptsY) && Array.isArray(pts) 
            && typeof(pts[0]) === "number" && typeof(ptsY[0]) === "number"
            && pts.length === ptsY.length)
        {
          // we have an array of X values in 'pts' and Y values in 'ptsY'
          splns = BuildSpline(pts, ptsY);
        }
        else
        {
          console.log("Type Error: bad argument for splineFit");
          return;
        }
      }
      else  
      {
        if (Array.isArray(pts))  // just 1 argument
        {
          if (typeof(pts[0]) === "number" && pts.length >= 4)
          {
            const xAry = [];
            const yAry = [];
            // we have data [x0, y0, x1, y1, ...]
            for (let i=0; i<pts.length; i+=2)
            {
              xAry.push(pts[i]);
              yAry.push(pts[i+1]);
            }
            // generate the array of natural spines to fit
            splns = BuildSpline(xAry, yAry);
          }
          else if (typeof(pts[0]) === "object" && pts.length >= 2 && pts[0].hasOwnProperty("x") && pts[0].hasOwnProperty("y"))
          {
            // we have data [{x: , y: }, {x: , y: }, ...]
            const xAry = pts.reduce((acc, pt)=>{acc.push(pt.x); return acc}, []);
            const yAry = pts.reduce((acc, pt)=>{acc.push(pt.y); return acc}, []);
            // generate the array of natural spines to fit
            splns = BuildSpline(xAry, yAry);
          }
          else
          {
            console.log("Type Error: bad argument for splineFit");
            return;
          }
        }
        else
        {
          console.log("Type Error: bad argument for splineFit");
          return;
        }
      }
  
      // make the Bezier curve through the data points
      const bezDataStr = splineToBezier2(splns);
  
      return new PathSVG(bezDataStr);
    };
    
    PathSVG.polyline = function(pts, ptsY) {
      function buildPolyLine(xPts, yPts)
      {
        const pLineAry = ["M", xPts[0], yPts[0], "L"];
        for (let i=0; i<xPts.length; i++)
        {
          pLineAry.push(xPts[i], yPts[i]);
        }
  
        return pLineAry;
      }
  
      let pLine;
      if (arguments.length === 2)
      {
        if (Array.isArray(ptsY) && Array.isArray(pts) 
            && typeof(pts[0]) === "number" && typeof(ptsY[0]) === "number"
            && pts.length === ptsY.length)
        {
          // we have an array of X values in 'pts' and Y values in 'ptsY'
          pLine = buildPolyLine(pts, ptsY);
        }
        else
        {
          console.log("Type Error: bad argument for PolyLine");
          return;
        }
      }
      else  
      {
        if (Array.isArray(pts))  // just 1 argument
        {
          if (typeof(pts[0]) === "number" && pts.length >= 4)
          {
            const xAry = [];
            const yAry = [];
            // we have data [x0, y0, x1, y1, ...]
            for (let i=0; i<pts.length; i+=2)
            {
              xAry.push(pts[i]);
              yAry.push(pts[i+1]);
            }
            // generate the array of natural spines to fit
            pLine = buildPolyLine(xAry, yAry);
          }
          else if (typeof(pts[0]) === "object" && pts.length >= 2 && pts[0].hasOwnProperty("x") && pts[0].hasOwnProperty("y"))
          {
            // we have data [{x: , y: }, {x: , y: }, ...]
            const xAry = pts.reduce((acc, pt)=>{acc.push(pt.x); return acc}, []);
            const yAry = pts.reduce((acc, pt)=>{acc.push(pt.y); return acc}, []);
            // generate the array of natural spines to fit
            pLine = buildPolyLine(xAry, yAry);
          }
          else
          {
            console.log("Type Error: bad argument for PolyLine");
            return;
          }
        }
        else
        {
          console.log("Type Error: bad argument for PolyLine");
          return;
        }
      }
  
      return new PathSVG(pLine);
    }; 
  
    class BezTrack
    {
      constructor(segVals)  // PathSVG.values array
      {
        const c = segVals;
        this.segPoints = [{x:c[0], y:c[1]}, {x:c[2], y:c[3]}, {x:c[4], y:c[5]}, {x:c[6], y:c[7]}];
        this.segLength = this._length(this.segPoints);
      }
  
      /*=============================================================================
      * _pointOnCubicBez calculates coords of a point on a cubic Bezier curve.
      * 'curve' is an array of 4 control points, 
      * eg [{x:10,y:20}, {x:50,y:50}, {x:100,y:100}, {x:120,y:100}]. 
      * 'location' is a decimal indicating the fractional distance along the curve. 
      * It should be a number from 0 to 1, inclusive.
      *----------------------------------------------------------------------------*/
      _pointOnCubicBez(curve, location){	
        let bezx = (t)=>curve[0].x*(1 - t)*(1 - t)*(1 - t)+curve[1].x*3*t*(1 - t)*(1 - t)+
                        curve[2].x*3*t*t*(1 - t)+curve[3].x*t*t*t;
        let bezy = (t)=>curve[0].y*(1 - t)*(1 - t)*(1 - t)+curve[1].y*3*t*(1 - t)*(1 - t)+
                        curve[2].y*3*t*t*(1 - t)+curve[3].y*t*t*t;
  
        return {x:bezx(location), y:bezy(location)};
      }
  
      _dist(p1, p2){
        return Math.sqrt((p1.x-p2.x)*(p1.x-p2.x) + (p1.y-p2.y)*(p1.y-p2.y));
      }
  
      _length(curve){
        var prev = this._pointOnCubicBez(curve, 0),
            tally = 0,
            curLoc = 0,
            direction = 1,
            cur = null;
  
        while (curLoc < 1) 
        {
          curLoc += (0.005 * direction);
          cur = this._pointOnCubicBez(curve, curLoc);
          tally += this._dist(cur, prev);	
          prev = cur;
        }
        return tally;
      }
  
      /*=======================================================================
      * _gradientAtPoint
      * returns the gradient and dy,dx components of the curve at the point. 
      *----------------------------------------------------------------------*/
      _gradientAtPoint(curve, location){
        let p1,	p2;
  
        if (location > 0.994)
        {
          p1 = this._pointOnCubicBez(curve, location-0.005);
          p2 = this._pointOnCubicBez(curve, location);
        }
        else
        {
          p1 = this._pointOnCubicBez(curve, location);
          p2 = this._pointOnCubicBez(curve, location+0.005);
        }
        const dy = p2.y - p1.y; 
        const dx = p2.x - p1.x;
        const dLen = Math.sqrt(dx*dx + dy*dy);
  
        return {angRad: Math.atan2(dy, dx), dx: dx/dLen, dy: dy/dLen};	
      }
  
      /*================================================================================
      * _pointAlongPath finds the point that is 'distance' along the path from start. 
      * This method returns both the x,y location of the point and also its 'location' 
      * (fractional distance along the path).
      *-------------------------------------------------------------------------------*/
      _pointAlongPath(curve, location, distance){
        const direction = distance > 0 ? 1 : -1,
              step = (0.005 * direction);      // 200 steps (0..1)
        let prev = this._pointOnCubicBez(curve, location),
            tally = 0,
            curLoc = location,
            cur = this._pointOnCubicBez(curve, location);
  
        while (tally < Math.abs(distance)) 
        {
          curLoc += step;
          cur = this._pointOnCubicBez(curve, curLoc);
          tally += this._dist(cur, prev);	
          prev = cur;
        }
  
        return {point:cur, location:curLoc, distance:distance};
      }
    }
  
    class LineTrack
    {
      constructor(segVals)   // PathSVG.values array
      {
        const c = segVals;
        this.segPoints = [{x:c[0], y:c[1]}, {x:c[2], y:c[3]}];
        this.segLength = Math.sqrt((c[2]-c[0])*(c[2]-c[0]) + (c[3]-c[1])*(c[3]-c[1]));
      }
  
      /*=======================================================================
      * _gradientAtPoint
      * returns the gradient and dy,dx components of the curve at point.
      *----------------------------------------------------------------------*/
      _gradientAtPoint(){
        const p = this.segPoints,
              dy = p[1].y - p[0].y, 
              dx = p[1].x - p[0].x;
  
        const dLen = Math.sqrt(dx*dx + dy*dy);
  
        return {angRad:Math.atan2(dy, dx), dx: dx/dLen, dy: dy/dLen};	
      }
  
      /*================================================================================
      * _pointAlongPath finds the point that is 'distance' along the path from start. 
      * This method returns both the x,y location of the point and also its 'location' 
      * (fractional distance along the path).
      *-------------------------------------------------------------------------------*/
      _pointAlongPath(line, location, distance){
        const p = this.segPoints;
        const frac = (distance - location)/this.segLength;
        const cur = {x: p[0].x+frac*(p[1].x - p[0].x), y: p[0].y+frac*(p[1].y - p[0].y)};
  
        return {point:cur, location:frac, distance:distance};
      }
    }
  
    class Track 
    {
      constructor(svgSegsAry)  // type PathSVG
      {
        this.segs = [];
        let initPos; 
        let pen;  // pen is following the current reference point
        for (let i=0; i<svgSegsAry.length; i++)
        {
          let pts;
          let seg = svgSegsAry[i];
          if (seg.type === "C")
          {
            pts = pen.concat(seg.values);  // give each segment a first 
            this.segs.push(new BezTrack(pts));
            pen = [seg.values[4], seg.values[5]];   // move pen to last bez end point
          }
          else if (seg.type === "L")
          {
            pts = pen.concat(seg.values);
            this.segs.push(new LineTrack(pts));
            pen = seg.values;
          }
          else if (seg.type === "Z")  
          {
            // check if the path was closed anyway
            if (pen[0] == initPos[0] && pen[1] == initPos[1]) 
              break;
            // make a line segment to close the path
            pts = pen.concat(initPos);
            this.segs.push(new LineTrack(pts));
            break;// should be last segment but if not, make it the last
          }
          else if (seg.type === "M")
          {
            initPos = svgSegsAry[i].values;  // restart a track section values is just [x,y]
            pen = svgSegsAry[i].values.slice(0);  // pen is following the current reference point
          } 
        }
        const add = (acc, curr)=>acc + curr.segLength;
        this.totalLength = this.segs.reduce(add, 0);
  
        // calculate lengths of each segment to know which segment keyTimes are in
        this.segEndDist = [];
        let endDist = 0;
        this.segs.forEach((seg)=>{
          endDist += seg.segLength;
          this.segEndDist.push(endDist);
        });
      }
      
      trkDistToPos(currDist){  // distance in world coords
        // convert a distance along track into a world coord location (get grad too)
        const tLen = this.totalLength;
        let currSeg,
            currStart = 0,
            currEnd = 0;
        for (let i=0; i<this.segEndDist.length; i++)
        {
          currSeg = this.segs[i];
          currEnd += currSeg.segLength;
          if (currEnd >= currDist) 
            break;
          currStart = currEnd; 
          if (currStart >= tLen)
          {
            // after resetting to start at seg0 the for loop is exited
            currSeg = this.segs[0];
            currEnd = currSeg.segLength;
            currStart = 0;
            currDist -= tLen;  
          }
        }
        // calc distance into segment
        const segDist = currDist - currStart;
        const posObj = currSeg._pointAlongPath(currSeg.segPoints, 0, segDist);
        const grad = currSeg._gradientAtPoint(currSeg.segPoints, posObj.location);
        
        return {x:posObj.point.x, y:posObj.point.y, gradient:grad.angRad, dx:grad.dx, dy:grad.dy};
      }
    }

  function Path2DObj()
  {
    this.p2dWC = null;    // Path2D object with coords in world coordinates
    this.p2dPX = null;    // Path2D with coords scaled for canvas raw pixel coord system
    this.length = 0;
  }
  
  function matrixIdent()
  {
    return new DOMMatrix();
  }

  function matrixMult(A, B)
  {
    return A.multiply(B); // mathematically A x B
  }

  function matrixClone(M) // reset to the identity matrix
  { 
    return new DOMMatrix(M);
  }

  function matrixRotate(M, degs)
  {
    // Rotation transform for column vectors:
    // Rotate by angle T (in radians)
    const T = -degs*Math.PI/180.0;
    const cosT = Math.cos(T);
    const sinT = Math.sin(T);
    const A = new DOMMatrix([cosT, sinT, -sinT, cosT, 0.0, 0.0]);

    return matrixMult(A, M);  // A x M
  } 

  function matrixSkew(M, degsH, degsV)
  {
    // Skew angles (in radians)
    const Th = degsH*Math.PI/180.0;
    const Tv = degsV*Math.PI/180.0;
    const htn = Math.tan(Th);
    const vtn = Math.tan(Tv);
    const A = new DOMMatrix([1.0, vtn, htn, 1.0, 0.0, 0.0]);

    return matrixMult(A, M);  // A x M
  }

  function matrixScale(M, sclX, sclY)
  {
    // Scale transform for column vectors:
    let A = new DOMMatrix([sclX, 0.0, 0.0, sclY, 0.0, 0.0]);

    return matrixMult(A, M);
  }

  function matrixTranslate(M, ofsX, ofsY)
  {
    // Scale transform for column vectors:
    let A = new DOMMatrix([1.0, 0.0, 0.0, 1.0, ofsX, ofsY]);
    
    return matrixMult(A, M);  // A x M
  }

  function matrixTransformPoint(M, p)
  {
    const px = p.x,
          py = p.y;

    return {x:px*M.a + py*M.c + M.e, y:px*M.b + py*M.d + M.f};  // M x p (p is a column vector [[x], [y], [1]])
  }

  function hitTest(gc, pathObj, csrX, csrY)
  {
    gc.ctx.save();       // save un-scaled
    pathObj.pthCmds.p2dPX = new Path2D();
    pathObj.pthCmds.p2dPX.addPath(pathObj.pthCmds.p2dWC, pathObj.netTfm);   // scaled to pixels for raw canvas coords
    const hit = gc.ctx.isPointInPath(pathObj.pthCmds.p2dPX, csrX, csrY);
/* 
// for diagnostics on hit region, uncomment
gc.ctx.strokeStyle = 'red';
gc.ctx.lineWidth = 3;
gc.ctx.stroke(pathObj.pthCmds.p2dPX);
 */
    gc.ctx.restore();

    return hit;
  }

  function initDragAndDrop(gc)
  {
    // calc top canvas at grab time since layers can come and go
    const nLrs = gc.bkgCanvas.layers.length;
    // find top canvas in the Stack, only top layer will catch events
    const topCvs = gc.bkgCanvas.layers[nLrs-1].cElem;

    function grabHandler(event){
      const rect = gc.cnvs.getBoundingClientRect();
      const csrX = event.clientX - rect.left;
      const csrY = event.clientY - rect.top;
      // run through all the registered objects and test if cursor pos is within their path
      loops:      // label to break out of nested loops
      for (let j = nLrs-1; j >= 0; j--)       // search top layer down the stack
      {
        const lyr = gc.bkgCanvas.layers[j];
        for (let k = lyr.dragObjects.length-1; k >= 0; k--)  // search from last drawn to first (underneath)
        {
          const testObj = lyr.dragObjects[k];
          if (hitTest(gc, testObj, csrX, csrY))
          {
            // call the grab handler for this object (check it is still enabled)
            if (testObj.dragNdrop)
            {
              testObj.dragNdrop.topCvs = topCvs;   // gc.bkgCanvas.layers[nLrs-1].cElem;
              testObj.dragNdrop.grab(event);
              break loops;
            }
          }
        }
      }
    }

    topCvs.onmousedown = (e)=>{grabHandler(e)};  
  } 

  class Drag2D 
  {
    constructor(type, dragFn, grabFn=null, dropFn=null, cancelFn=null) {
      // version of drop that can be called from an app to stop a drag before the mouseup event
      const cancelDragFn = ()=>
      {
        this.topCvs.onmouseup = null;
        this.topCvs.onmouseout = null;
        this.topCvs.onmousemove = null;
        if (this.dropCallback)
        {
          this.dropCallback.call(this.cgo, this.eventData);   // call with most recent drag data
        }
      };

      this.dndType = type;          // "drag" or "click"
      this.cgo = null;              // filled in by render
      this.layer = null;            // filled in by render
      this.topCvs = null;
      this.grabCallback = grabFn;
      this.dragCallback = dragFn;
      this.dropCallback = dropFn;
      this.cancelCallback = cancelFn;
      this.eventData = {
        gc: null,
        target: null,               // filled in by render
        pointerPos: {x:0, y:0},     // world coords
        savPointerPos: {x:0, y:0},  // position of cursor when target last drawn 
        dragPos: {x:0, y:0},
        dragOfs: {x:0, y:0},
        grabCsrPos: {x:0, y:0},     // world coords
        grabAngle: 0,
        dragAngle: 0,               // degrees
        dragOfsAngle: 0,
        cancelDrag: cancelDragFn
      }
    }

    mouseupHandler(event){
      this.topCvs.onmouseup = null;
      this.topCvs.onmouseout = null;
      this.topCvs.onmousemove = null;
      this.eventData.gc = this.cgo;
      if (this.dndType === "click")
      {
        // check if mouse moved outside object after mousedown and before mouseup (ie cancel onclick)
        const rect = this.cgo.cnvs.getBoundingClientRect();  // find the canvas boundaries
        const csrX = event.clientX - rect.left;
        const csrY = event.clientY - rect.top;
        const inside = hitTest(this.cgo, this.eventData.target, csrX, csrY);
        if (!inside)
          {
            if (this.cancelCallback)
            {
              this.cancelCallback.call(this.cgo, this.eventData);   // call in the scope of the Cango context
            }
            return;  // cancelled, and no onclick callback
          }
        }
      if (this.dropCallback)
      {
        this.dropCallback.call(this.cgo, this.eventData);   // call in the scope of the Cango context
      }
    }

    grab(event){
      const isoWC_to_yWC = Math.abs(this.cgo.yscl/this.cgo.xscl);
      const target = this.eventData.target;
      // calc top canvas at grab time since layers can come and go
      const nLrs = this.cgo.bkgCanvas.layers.length;
      this.topCvs = this.cgo.bkgCanvas.layers[nLrs-1].cElem;

      this.topCvs.onmouseup = (e)=>{this.mouseupHandler(e)};
      this.topCvs.onmouseout = (e)=>{this.drop(e)};
      const csrPosWC = this.cgo.getCursorPosWC(event);      // update mouse pos to pass to the owner
      this.eventData.gc = this.cgo;
      this.eventData.grabCsrPos.x = csrPosWC.x - target.dwgOrg.x;
      this.eventData.grabCsrPos.y = csrPosWC.y - target.dwgOrg.y;
      const csrX = csrPosWC.x - target.dwgOrg.x;
      const csrY = csrPosWC.y - target.dwgOrg.y;
      this.eventData.grabAngle = Math.atan2(csrY*isoWC_to_yWC, csrX)*180/Math.PI;
      this.eventData.savPointerPos.x = csrPosWC.x;   
      this.eventData.savPointerPos.y = csrPosWC.y;   
      this.eventData.pointerPos.x = csrPosWC.x;   
      this.eventData.pointerPos.y = csrPosWC.y;   
      this.eventData.dragPos.x = 0;
      this.eventData.dragPos.y = 0;
      this.eventData.dragOfs.x = 0;
      this.eventData.dragOfs.y = 0;
      this.eventData.dragAngle = 0;
      this.eventData.dragOfsAngle = 0;
  
      target.dNdActive = true;
      if (this.grabCallback)
      {
        this.grabCallback.call(this.cgo, this.eventData);   // call in the scope of the Cango context
      }
      this.topCvs.onmousemove = (event)=>{this.drag(event);};
      event.preventDefault();
      return false;
    }

    drag(event){
      const isoWC_to_yWC = Math.abs(this.cgo.yscl/this.cgo.xscl);
      const target = this.eventData.target;
      if (this.dragCallback)
      {
        const csrPosWC = this.cgo.getCursorPosWC(event);  // update mouse pos to pass to the owner
        this.eventData.gc = this.cgo;
        // save the last 'as drawn' values
        this.eventData.savPointerPos.x = this.eventData.pointerPos.x;
        this.eventData.savPointerPos.y = this.eventData.pointerPos.y;
        this.eventData.savAngle = this.eventData.dragAngle;    // save the last drag angle

        this.eventData.pointerPos.x = csrPosWC.x;
        this.eventData.pointerPos.y = csrPosWC.y;
        this.eventData.dragPos.x = csrPosWC.x - this.eventData.grabCsrPos.x; 
        this.eventData.dragPos.y = csrPosWC.y - this.eventData.grabCsrPos.y; 
        this.eventData.dragOfs.x = csrPosWC.x  - this.eventData.savPointerPos.x;
        this.eventData.dragOfs.y = csrPosWC.y  - this.eventData.savPointerPos.y;
        // To calculate the Z axis rotation about the target drawing origin
        // the cylinder radius is set by the cursor distance from the dwgOrg
        const csrX = csrPosWC.x - target.dwgOrg.x;
        const csrY = csrPosWC.y - target.dwgOrg.y;
        const angZ = Math.atan2(csrY*isoWC_to_yWC, csrX) * 180/Math.PI;
        this.eventData.dragAngle = angZ - this.eventData.grabAngle;  // angle in degs
        this.eventData.dragOfsAngle = this.eventData.dragAngle - this.eventData.savAngle;   // offset from grab

        this.dragCallback.call(this.cgo, this.eventData);   // call in the scope of the Cango context
      }
    }

    drop(event){
      this.topCvs.onmouseup = null;
      this.topCvs.onmouseout = null;
      this.topCvs.onmousemove = null;
      this.eventData.target.dNdActive = false;
      this.eventData.gc = this.cgo;
      if (this.dropCallback)
      {
        this.dropCallback.call(this.cgo, this.eventData);   // call in the scope of the Cango context
      }
    }
  }

  LinearGradient = class 
  {
    constructor(p1x, p1y, p2x, p2y)
    {
      this.grad = {x1:p1x, y1:p1y, x2:p2x, y2:p2y};
      this.colorStops = [];
    }
    
    addColorStop(stop, color)
    {
      this.colorStops.push({stop:stop, color:color});
    }
  }

  RadialGradient = class 
  { 
    constructor(p1x, p1y, r1, p2x, p2y, r2)
    {
      this.grad = {x1:p1x, y1:p1y, r1:r1, x2:p2x, y2:p2y, r2:r2};
      this.colorStops = [];
    }

    addColorStop(stop, color)
    {
      this.colorStops.push({stop:stop, color:color});
    }
  }

  class TfmDescriptor
  {
    constructor(type, ...argAry)  // type and the rest
    {
      this.type = type;
      this.args = argAry;  // other args as an array
    }
  }

  Group = class 
  {
    constructor(...args)
    {
      this.type = "GRP";                    // enum of type to instruct the render method
      this.parent = null;                   // pointer to parent Group (if not undefined)
      this.children = [];                   // only Groups have children
      this.dwgOrg = {x:0, y:0};             // drawing origin (0,0) may get translated
      this.ofsTfmAry = [];                  // soft transforms applied to this Group 
      this.ofsTfmMat = matrixIdent();       // ofsTfmsAry as a matrix, cleared after render 
      this.currOfsTfmMat = matrixIdent();
      this.netTfmMat = matrixIdent();       // inherited ofsTfmMat mult by own ofsTfmMat  
      this.dragNdropHandlers = null;        // array of DnD handlers to be passed to newly added children
      this.dNdActive = false;
      // add any objects passed by forwarding them to addObj
      this.addObj(args);  // args is an array from the constructor 'rest'
    }

    // Groups can pass on hard transform properties to all the children (but not style properties) 
    addTransformProperty(propertyName, value)
    {
      const transforms = ["x", "y", "rot", "scl", "flip"];
      // set Obj2D property recursively
      const iterate = (grp)=>{
        grp.children.forEach((childNode)=>{
          if (childNode.type === "GRP")
          {
            iterate(childNode);
          }
          else   // Obj2D
          {
            if (transforms.includes(propertyName.toLowerCase()))
              setPropertyFn.call(childNode, propertyName, value);
          }
        });
      }

      iterate(this);
    }

    deleteObj(obj)
    {
      // remove from children array
      const idx = this.children.indexOf(obj);

      if (idx >= 0)
      {
        this.children.splice(idx, 1);
        obj.parent = null;
      }
    }

    addObj(...args)  // the 'rest' returns an Array
    {
      const iterate = (argAry)=>{
        argAry.forEach((elem)=>{
          if (Array.isArray(elem))
          {
            iterate(elem);
          }
          else   // Obj2D or Group
          {
            if (!elem || (!types.includes(elem.type)))  // don't add undefined or non-Obj2D
            {
              console.warn("Type Error: Group.addObj: argument", elem);
              return;
            }
            elem.parent = this;            // now its a free agent link it to this group
            this.children.push(elem);
            // enable drag and drop if this group has drag
            if (!elem.dragNdrop && this.dragNdropHandlers)
            {
              elem.enableDrag.apply(elem, this.dragNdropHandlers);
              elem.dragNdrop.eventData.target = this;     // the Group is the target being dragged
            }
          }
        });
      }

      iterate(args);
    }

    dup()
    {
      const newGrp = new Group();
      this.children.forEach((childNode)=>{
        newGrp.addObj(childNode.dup());
      });

      return newGrp;
    }

   /*====================================================
    * Recursively add a Drag object to Obj2D descendants 
    * of a Group.
    * When rendered all these Obj2D will be added to 
    * dragObjects to be checked for mousedown events
    *---------------------------------------------------*/
    enableDrag(dragFn, grabFn, dropFn, cancelFn)
    {
      const iterate = (grp)=>{
        grp.children.forEach((childNode)=>{
          if (childNode.type === "GRP")
          {
            iterate(childNode);
          }
          else if (childNode.dragNdrop === null)    // don't over-write if its already assigned a handler
          {
            childNode.enableDrag(dragFn, grabFn, dropFn, cancelFn);
            childNode.dragNdrop.eventData.target = this;     // the Group is the target being dragged
          }
        });
      }

      this.dragNdropHandlers = arguments;
      iterate(this);
    }

    /*======================================
    * Disable dragging on Obj2D descendants
    *-------------------------------------*/
    disableDrag()
    {
      const iterate = (grp)=>{
        grp.children.forEach((childNode)=>{
          if (childNode.type === "GRP")
          {
            iterate(childNode);
          }
          else
          {
            childNode.disableDrag();
          }
        });
      }

      this.dragNdropHandlers = null;
      iterate(this);
    }

   /*======================================================
    * Recursively add a Drag object to Obj2D descendants 
    * of a Group.
    * When rendered all these Obj2D will be added to 
    * dragObjects to be checked for mouseup (click) events
    * and (optional) mousedown events
    *-----------------------------------------------------*/
   enableClick(clickFn, downEvtFn, cancelFn)
   {
     const iterate = (grp)=>{
        grp.children.forEach((childNode)=>{
          if (childNode.type === "GRP")
          {
            iterate(childNode);
          }
          else if (childNode.dragNdrop === null)    // don't over-write if its already assigned a handler
          {
            childNode.enableClick(clickFn, downEvtFn, cancelFn);
            childNode.dragNdrop.eventData.target = this;     // the Group is the target being clicked
          }
        });
      }

      this.dragNdropHandlers = [null, downEvtFn, clickFn, cancelFn];
      iterate(this);
    }

   /*======================================
    * Disable onclick for Obj2D descendants
    *-------------------------------------*/
    disableClick()
    {
      const iterate = (grp)=>{
        grp.children.forEach((childNode)=>{
          if (childNode.type === "GRP")
          {
            iterate(childNode);
          }
          else
          {
            childNode.disableClick();
          }
        });
      }

      this.dragNdropHandlers = null;
      iterate(this);
    }

   /*=========================================================
    * Add a translation transform to the Group's OfsTfmAry.
    *--------------------------------------------------------*/
    translate(x=0, y=0)
    {
      const trnsDstr = new TfmDescriptor("TRN", x, y);
      this.ofsTfmAry.push(trnsDstr);
      return this;
    }

   /*=========================================================
    * Add a scale transform to the Group's OfsTfmAry.
    *--------------------------------------------------------*/
    scale(xScl, yScl)
    {
      const sx = xScl || 0.001,
            sy = yScl || sx;

      const sclDstr = new TfmDescriptor("SCL", sx, sy);
      this.ofsTfmAry.push(sclDstr);
      return this;
    }

   /*=========================================================
    * Add a rotation transform to the Group's OfsTfmAry.
    *--------------------------------------------------------*/
    rotate(degs=0)
    {
      const rotDstr = new TfmDescriptor("ROT", degs);
      this.ofsTfmAry.push(rotDstr);
      return this;
    }

   /*=========================================================
    * Add a skew transform to the Group's OfsTfmAry.
    *--------------------------------------------------------*/
    skew(degsH=0, degsV=0)
    {
      const skwDstr = new TfmDescriptor("SKW", degsH, degsV);
      this.ofsTfmAry.push(skwDstr);
      return this;
    }

    transformRestore()
    {
      const iterate = (grp)=>{
        grp.children.forEach((childNode)=>{
          if (childNode.type === "GRP")
          {
            childNode.transformRestore();
            iterate(childNode);
          }
          else  // Obj2D
          {
            childNode.transformRestore();
          }
        });
      }

      this.ofsTfmMat = matrixClone(this.currOfsTfmMat);

      iterate(this);
    }
  }      /*  Group */

  function setPropertyFn(propertyName, value)
  {
    const lorgVals = [1, 2, 3, 4, 5, 6, 7, 8, 9];

    if ((typeof propertyName !== "string")||(value === undefined))
    {
      return;
    }

    switch (propertyName.toLowerCase())
    {
      case "fillrule":
        if (typeof value !== "string")
        {
          return;
        }
        if ((value === "evenodd")||(value ==="nonzero"))
        {
          this.fillRule = value;
        }
        break;
      case "fillcolor":
        this.fillCol = value;
        break;
      case "strokecolor":
        this.strokeCol = value;
        break;
      case "linewidth":
      case "strokewidth":      // for backward compatibility
        if ((typeof value === "number")&&(value > 0))
        {
          this.lineWidth = value;
        }
        break;
      case "linewidthwc":
        if ((typeof value === "number")&&(value > 0))
        {
          this.lineWidthWC = value;
        }
        break;
      case "linecap":
        if (typeof value !== "string")
        {
          return;
        }
        if ((value === "butt")||(value ==="round")||(value === "square"))
        {
          this.lineCap = value;
        }
        break;
      case "linejoin":
        if (typeof value !== "string")
        {
          return;
        }
        if ((value === "bevel")||(value ==="round")||(value === "miter"))
        {
          this.lineJoin = value;
        }
        break;
      case "iso":
      case "isotropic":
        if ((value == true)||(value === 'iso')||(value === 'isotropic'))
        {
          this.iso = true;
        }
        else
        {
          this.iso = false;
        }
        break;
      case "dashed":
        if (Array.isArray(value) && value[0])
        {
          this.dashed = value;
        }
        else     // ctx.setLineDash([]) will clear dashed settings
        {
          this.dashed = [];
        }
        break;
      case "dashoffset":
        this.dashOffset = value || 0;
        break;
      case "border":
        if (value === true)
        {
          this.border = true;
        }
        if (value === false)
        {
          this.border = false;
        }
        break;
      case "fontsize":
        if ((typeof value === "number")&&(value > 0))
        {
          this.fontSize = value;
        }
        break;
      case "fontsizewc":
        if ((typeof value === "number")&&(value > 0))
        {
          this.fontSizeWC = value;
        }
        break;
      case "fontweight":
        if ((typeof value === "string")||((typeof value === "number")&&(value>=100)&&(value<=900)))
        {
          this.fontWeight = value;
        }
        break;
      case "fontfamily":
        if (typeof value === "string")
        {
          this.fontFamily = value;
        }
        break;
      case "bgfillcolor":
        this.bgFillColor = value;
        break;
      case "imgwidth":
        this.imgWidth = Math.abs(value);
        break;
      case "imgheight":
        this.imgHeight = Math.abs(value);
        break;
      case "lorg":
        if (lorgVals.indexOf(value) !== -1)
        {
          this.lorg = value;
        }
        break;
      case "shadowoffsetx":
        this.shadowOffsetX = value || 0;
        break;
      case "shadowoffsety":
        this.shadowOffsetY = value || 0;
        break;
      case "shadowblur":
        this.shadowBlur = value || 0;
        break;
      case "shadowcolor":
        this.shadowColor = value;
        break;
      case "skwH":
        {
          const skwHDstr = new TfmDescriptor("SKW", value, 0);
          this.hardTfmAry.push(skwHDstr);
        }
        break;
      case "skwV":
        {
          const skwVDstr = new TfmDescriptor("SKW", 0, value);
          this.hardTfmAry.push(skwVDstr);
        }
        break;
      case "scl":
        if (Array.isArray(value))
        {
          if (!value[0]) 
            {
              console.warn("Range Error: invalid scale value");
            }
            else
            {          
              const sclX = value[0];
              const sclY = (value[1])? value[1]: sclX;
              const sclDstr = new TfmDescriptor("SCL", sclX, sclY);
              this.hardTfmAry.push(sclDstr);
            }
        }
        else
        {
          if (!value) 
          {
            console.warn("Range Error: invalid scale value");
          }
          else
          {
            const scl = value;
            const sclDstr = new TfmDescriptor("SCL", scl, scl);
            this.hardTfmAry.push(sclDstr);
          }
        }
        break;
        case "rot":
          {
            const rotDstr = new TfmDescriptor("ROT", value);
            this.hardTfmAry.push(rotDstr);
          }
          break;
        case "x":
          {
            const trnsXDstr = new TfmDescriptor("TRN", value, 0);
            this.hardTfmAry.push(trnsXDstr);
          }
          break;
        case "y":
          {
            const trnsYDstr = new TfmDescriptor("TRN", 0, value);
            this.hardTfmAry.push(trnsYDstr);
          }
          break;
        case "flip":
        if (typeof value === "string")
        {
          if (value[0] == "v" || value[0] == "V")
          {
            const flpDstr = new TfmDescriptor("SCL", 1, -1);
            this.hardTfmAry.push(flpDstr);
          }
          else if (value[0] == "h" || value[0] == "H")
          {
            const flpDstr = new TfmDescriptor("SCL", -1, 1);
            this.hardTfmAry.push(flpDstr);
          }
        }
        break;
      default:
        break;
    }
  }

  function getStylePropertyFn(propertyName)
  {
    if (typeof propertyName !== "string")
    {
      return undefined;
    }

    switch (propertyName.toLowerCase())
    {
      case "fillrule":
        return this.fillRule;
      case "fillcolor":
        return this.fillCol;
      case "strokecolor":
        return this.strokeCol;
      case "linewidth":
      case "strokewidth": 
        return this.lineWidth;
      case "linewidthwc":
        return  this.lineWidthWC;
      case "linecap":
        return this.lineCap;
      case "linejoin":
        return this.lineJoin;
      case "iso":
      case "isotropic":
        return this.iso;
      case "dashed":
        return this.dashed;
      case "dashoffset":
        return this.dashOffset;
      case "border":
        return this.border;
      case "fontsize":
        return this.fontSize;
      case "fontsizewc":
        return this.fontSizeWC;
      case "fontweight":
        return this.fontWeight;
      case "fontfamily":
        return this.fontFamily;
      case "bgfillcolor":
        return this.bgFillColor;
      case "imgwidth":
        return this.imgWidth;
      case "imgheight":
        return this.imgHeight;
      case "lorg":
        return this.lorg;
      case "shadowoffsetx":
        return this.shadowOffsetX;
      case "shadowoffsety":
        return this.shadowOffsetY;
      case "shadowblur":
        return this.shadowBlur;
      case "shadowcolor":
        return this.shadowColor;
      default:
        return undefined;
    }
  }

  function dupCommon(newObj, org)  // Object of the correct type
  {
    // duplicate the common prperties
    if (org.pthCmds.p2dWC)
    {
      newObj.pthCmds.p2dWC = new Path2D(org.pthCmds.p2dWC);
      newObj.pthCmds.length = org.pthCmds.length;
    }
    newObj.parent = null;                      // pointer to parent group if any
    newObj.dwgOrg = structuredClone(org.dwgOrg);
    newObj.hardTfmAry = structuredClone(org.hardTfmAry); // hard offset from any parent Group's transform
    // do not duplicate dynamic transform
    newObj.fillRule = org.fillRule;            // for SHAPE
    newObj.fillCol = org.fillCol;              // for SHAPE
    newObj.border = org.border;
    newObj.strokeCol = org.strokeCol;
    newObj.lineWidth = org.lineWidth;
    newObj.lineWidthWC = org.lineWidthWC;
    newObj.lineCap = org.lineCap;
    newObj.lineJoin = org.lineJoin;
    newObj.iso = org.iso;
    newObj.clearFlag = org.clearFlag;

    newObj.shadowOffsetX = org.shadowOffsetX;
    newObj.shadowOffsetY = org.shadowOffsetY;
    newObj.shadowBlur = org.shadowBlur;
    newObj.shadowColor = org.shadowColor;

    newObj.dashed = structuredClone(org.dashed);
    newObj.dashOffset = org.dashOffset;
    // The other objects are dynamic, calculated at render
  }

  class Obj2D
  { 
    constructor()
    {
      this.iso = true;                      // default for ClipMask, Shape, Img, Text
      this.parent = null;                   // pointer to parent Group if any
      this.dwgOrg = {x:0, y:0};             // drawing origin (0,0) may get translated
      this.ofsTfmAry = [];                  // soft transforms cleared after render
      this.ofsTfmMat = matrixIdent();       // ofsTfmsAry as a matrix, cleared after render 
      this.currOfsTfmMat = matrixIdent();   // copy of ofsTfmMat as drawn
      this.hardTfmAry = [];                 // hard transforms not cleared after render
      this.netTfm = matrixIdent();          // the transform matrix to be applied prior to rendering
      this.dragNdrop = null;
      this.dNdActive = false;
    }

    setStyleProperty(prop, val)
    {
      const transforms = ["x", "y", "rot", "scl", "flip"];

      if (!transforms.includes(prop.toLowerCase()))
      {
        setPropertyFn.call(this, prop.toLowerCase(), val);
      }
    }

    getStyleProperty(prop)
    {
      const transforms = ["x", "y", "rot", "scl", "flip"];

      if (!transforms.includes(prop.toLowerCase()))
      {
        return getStylePropertyFn.call(this, prop.toLowerCase());
      }
    }

    addTransformProperty(prop, val)
    {
      const transforms = ["x", "y", "rot", "scl", "flip"];
      
      if (transforms.includes(prop.toLowerCase()))
      {
        setPropertyFn.call(this, prop, val);
      }    
    }

    enableDrag(dragFn, grabFn, dropFn)
    {
      this.dragNdrop = new Drag2D("drag", dragFn, grabFn, dropFn);
      // fill in the Drag2D properties for use by callBacks
      this.dragNdrop.eventData.target = this;
    }

    disableDrag()
    {
      if (this.dragNdrop && this.dragNdrop.layer)
      {
        // remove this object from array to be checked on mousedown
        const aidx = this.dragNdrop.layer.dragObjects.indexOf(this);
        this.dragNdrop.layer.dragObjects.splice(aidx, 1);
        this.dragNdrop = null;
      }
    }

    enableClick(clickFn, downEvtFn, cancelFn)
    {
      this.dragNdrop = new Drag2D("click", null, downEvtFn, clickFn, cancelFn);
      // fill in the Drag2D properties for use by callbacks
      this.dragNdrop.eventData.target = this;
    }

    disableClick()
    {
      this.disableDrag();
    }

   /*=========================================================
    * Add a translation transform to the Obj2D's OfsTfmAry.
    *--------------------------------------------------------*/
    translate(x=0, y=0)
    {
      const trnsDstr = new TfmDescriptor("TRN", x, y);
      this.ofsTfmAry.push(trnsDstr);
      return this;
    }

   /*=========================================================
    * Add a scale transform to the Obj2D's OfsTfmAry.
    *--------------------------------------------------------*/
    scale(xScl, yScl)
    {
      if (!xScl) 
        {
          console.warn("Range Error: invalid scale value")
          return;
        }
        const sx = xScl;
        const sy = yScl || sx;
      
      const sclDstr = new TfmDescriptor("SCL", sx, sy);
      this.ofsTfmAry.push(sclDstr);
      return this;
    }
    
   /*=========================================================
    * Add a rotation transform to the Obj2D's OfsTfmAry.
    *--------------------------------------------------------*/
    rotate(degs=0)
    {
      const rotDstr = new TfmDescriptor("ROT", degs);
      this.ofsTfmAry.push(rotDstr);
      return this;
    }

   /*=========================================================
    * Add a skew transform to the Obj2D's OfsTfmAry.
    *--------------------------------------------------------*/
    skew(degH=0, degV=0)
    {
      const skwDstr = new TfmDescriptor("SKW", degH, degV);
      this.ofsTfmAry.push(skwDstr);
      return this;
    }

    transformRestore()
    {
      this.ofsTfmMat = matrixClone(this.currOfsTfmMat);
    }
  }

  ClipMask = class extends Obj2D
  {  
    constructor(pathDef, opt = {})
    {
      super();
      this.type = "CLIP";
      this.pthCmds = new Path2DObj();   
      this.fillRule = "nonzero";
      this.fillCol = null;
      this.border = false;    // ClipMask can have a border (half width showing)
      this.strokeCol = null;
      this.lineWidth = null;
      this.lineWidthWC = null;
      this.lineCap = null;
      this.lineJoin = null;
      this.savScale = 1; 
      // drop shadow properties
      this.shadowOffsetX = 0;
      this.shadowOffsetY = 0;
      this.shadowBlur = 0;
      this.shadowColor = "#000000";
      // dashed line properties
      this.dashed = [];
      this.dashOffset = 0;
  
      this.setDescriptor(pathDef);   // sets this.pthCmds

      for (const prop in opt)
      {
        if (opt[prop] !== undefined) // own property, not inherited from prototype
        {
          setPropertyFn.call(this, prop, opt[prop]);
        }   
      }
    }

    setDescriptor(commands)
    {
      if (typeof PathSVG !== 'undefined' && PathSVG !== null && commands instanceof PathSVG)
      {
        const str = commands.toString(5); 
        this.pthCmds.p2dWC = new Path2D(str);  
        this.pthCmds.length = str.length;  // used for warning if length == 0
      }
      else if (commands instanceof Path2D)
      {
        this.pthCmds.p2dWC = commands;
        // to detect draw empty objects set the length pthCmds.length=0 this will generate a warning
        this.pthCmds.length = 1;
      }
      else if ((typeof commands === "string") && commands.length)  // a string will be svg commands
      {
        const pathStr = commands.replace(/\,/g, " ");  // commas cause trouble, replace with spaces
        this.pthCmds.p2dWC = new Path2D(pathStr);
        this.pthCmds.length = pathStr.length;    // used for warning if length == 0
      }
      else if (commands && commands.length)  // non-empty array 
      {
        // check typed Array views etc, convert to real Array
        if (ArrayBuffer.isView(commands))    
        {
          commands = Array.from(commands);  
        }
        if (Array.isArray(commands))
        {
          let str = "";
          if (typeof(commands[0]) === "number")  // its an Array of numbers
          {
            str = "M "+commands.join(" ");  // insert 'M' command so its valid SVG
            this.pthCmds.p2dWC = new Path2D(str);
          }
          else
          {
            str = commands.join(" "); 
            this.pthCmds.p2dWC = new Path2D(str);  // simple conversion to svg String
          }
          this.pthCmds.length = str.length;  // used for warning if length == 0
        }
      }
    }

    getProperty(propName)
    {
      return getPropertyFn.call(this, propName);
    }

    dup()
    {
      const newObj = new ClipMask();
      dupCommon(newObj, this); 
      // The other objects are dynamic, calculated at render
  
      return newObj;         // return a object which inherits Obj2D properties
    }

    paint(gc)
    {
      // if empty array was passed as mask definition then reset clip to full canvas
      if (!this.pthCmds.length)
      {
        gc.resetClip();
        return;
      }
  
      gc.ctx.save();   // save context which has no clip mask (not restored locally)
      gc.clipCount += 1;
      this.pthCmds.p2dPX = new Path2D();
      this.pthCmds.p2dPX.addPath(this.pthCmds.p2dWC, this.netTfm);   // scaled to pixels for raw canvas coords
      gc.ctx.clip(this.pthCmds.p2dPX, this.fillRule);  // activate the clip mask, context is raw pixels default styles
    } 
  }

  Path = class extends ClipMask
  {
    constructor(commands, opt = {})
    {
      super(commands, opt);
      this.type = "PATH";               // type string to instruct the render method
      // only other difference is the default value for 'iso' property
      if (opt["iso"] !== undefined)
      {
        this.setStyleProperty("iso", opt.iso);
      }
      else if (opt["isotropic"] !== undefined)
      {
        this.setStyleProperty("iso", opt.isotropic);
      }
      else
      {
        this.iso = false;   // default false
      }
    }

    dup(){
      const newObj = new Path();
      dupCommon(newObj, this);

      return newObj;
    }

    paint(gc)
    {
      if (!this.pthCmds.length)
      {
        console.warn("Type Error: render Path descriptor");
        return;
      }
        
      // set up all the color 
      const col = this.strokeCol || gc.strokeColDef;
      let stkCol = col;
      if (col instanceof LinearGradient)
      {
        stkCol = gc.genLinGradPX(col, this);
      }
      else if (col instanceof RadialGradient)
      {
        stkCol = gc.genRadGradPX(col, this);
      }
      gc.ctx.save();   // save raw pixel context
      // apply the transforms and map from world to pixel coords
      this.pthCmds.p2dPX = new Path2D();
      this.pthCmds.p2dPX.addPath(this.pthCmds.p2dWC, this.netTfm);   // scale to pixels to use for stroke()
      gc.ctx.restore();  // back to raw pixels
      
      gc.ctx.save();   // save default styles, still raw pixels
      gc.dropShadow(this);    // set up dropShadow if any
  
      if (this.border) // use drop shadows for Path not border
      {
        gc.dropShadow(); 
      }
      // handle dashed lines
      if (Array.isArray(this.dashed) && this.dashed.length)
      {
        gc.ctx.setLineDash(this.dashed);
        gc.ctx.lineDashOffset = this.dashOffset || 0;
      }
      if (!this.orgXscl) this.orgXscl = gc.xscl;
      const zmScl = gc.xscl/this.orgXscl;
      // support for zoom and pan changing line width
      if (this.lineWidthWC)
      {
        gc.ctx.lineWidth = this.lineWidthWC*this.savScale*gc.xscl;   // lineWidth in world coords so scale to px
      }
      else
      {
        gc.ctx.lineWidth = this.lineWidth*zmScl || gc.lineWidthDef*zmScl; // lineWidth in pixels (/orgXscl to get to WC)
      }
      gc.ctx.strokeStyle = stkCol;
      gc.ctx.lineCap = this.lineCap || gc.lineCapDef;
      gc.ctx.lineJoin = this.lineJoin || gc.lineJoinDef;
      gc.ctx.stroke(this.pthCmds.p2dPX); // stroke the current path
      gc.ctx.setLineDash([]);            // clean up dashes (they are not reset by save/restore)
      gc.ctx.lineDashOffset = 0;
      gc.ctx.restore();                  // back to default styles, still raw pixels
  
      if (this.dragNdrop !== null)
      {
        initDragAndDrop(gc);
        gc.handleDnD(this);
      }
    } 
  }

  Shape = class extends ClipMask
  {
    constructor(commands, opt = {})
    {
      super(commands, opt);
      this.type = "SHAPE";
      this.clearFlag = false;  // private flag for clearShape method
    }

    dup(){
      const newObj = new Shape();
      dupCommon(newObj, this);

      return newObj;
    }

    paint(gc)
    {
      if (!this.pthCmds.length)
      {
        console.warn("Type Error: render Shape descriptor");
        return;
      }

      // set up all the colors
      let col = this.fillCol || gc.fillColDef;
      let filCol = col;
      if (col instanceof LinearGradient)
      {
        filCol = gc.genLinGradPX(col, this);
      }
      else if (col instanceof RadialGradient)
      {
        filCol = gc.genRadGradPX(col, this);
      }
      gc.ctx.save();   // save raw pixel context
      // apply the transforms and map from world to pixel coords
      this.pthCmds.p2dPX = new Path2D();
      this.pthCmds.p2dPX.addPath(this.pthCmds.p2dWC, this.netTfm);   // scale to pixels to use for stroke()
      gc.ctx.restore();  // back to raw pixels
      
      gc.ctx.save();   // save default styles, still raw pixels
      gc.dropShadow(this);    // set up dropShadow if any
      if (this.clearFlag)
      {
        gc.ctx.save();  
        gc.ctx.globalCompositeOperation = "destination-out";  // clear canvas inside the this
        gc.ctx.fill(this.pthCmds.p2dPX, this.fillRule);
        //=============================================================================
        // Workaround for Chrome/Edge bug: "ragged edge on destination-out fill"
        gc.ctx.lineWidth = 1.5;
        gc.ctx.stroke(); 
        //=============================================================================
        gc.ctx.restore();
      }
      else
      {
        gc.ctx.fillStyle = filCol;
        gc.ctx.fill(this.pthCmds.p2dPX, this.fillRule);
      }
  
      if (this.border)
      {
        gc.dropShadow(); 
        col = this.strokeCol || gc.strokeColDef;
        let stkCol = col;
        if (col instanceof LinearGradient)
        {
          stkCol = gc.genLinGradPX(col, this);
        }
        else if (col instanceof RadialGradient)
        {
          stkCol = gc.genRadGradPX(col, this);
        }
        // handle dashed lines
        if (Array.isArray(this.dashed) && this.dashed.length)
        {
          gc.ctx.setLineDash(this.dashed);
          gc.ctx.lineDashOffset = this.dashOffset || 0;
        }
        // support for zoom and pan changing line width
        if (!this.orgXscl) this.orgXscl = gc.xscl;
        const zmScl = gc.xscl/this.orgXscl;
        if (this.lineWidthWC)   // lineWidth in world coords
        {
          gc.ctx.lineWidth = this.lineWidthWC*this.savScale*gc.xscl; // scale to px
        }
        else  // lineWidth in pixels
        {
          gc.ctx.lineWidth = this.lineWidth*zmScl || gc.lineWidthDef*zmScl;
        }
 
        gc.ctx.strokeStyle = stkCol;
        gc.ctx.lineCap = this.lineCap || gc.lineCapDef;
        gc.ctx.lineJoin = this.lineJoin || gc.lineJoinDef;
        gc.ctx.stroke(this.pthCmds.p2dPX);
        gc.ctx.setLineDash([]);   // clean up dashes (they are not reset by save/restore)
        gc.ctx.lineDashOffset = 0;
      }
      gc.ctx.restore();           // back to default styles, still raw pixels
  
      if (this.dragNdrop !== null)
      {
        initDragAndDrop(gc);
        gc.handleDnD(this);
      }
    }  
  }

  Img = class extends Obj2D
  {
    constructor(imgDef, opt = {})
    {
      super();
      this.type = "IMG";

      this.srcX = 0;    // these get changed if Image cropped
      this.srcY = 0;    // so they shouldn't be initialize after setDescriptor
      this.srcWid = 0;
      this.srcHgt = 0;

      this.setDescriptor(imgDef);

      this.pthCmds = new Path2DObj();   // Path2D holding the img bounding box
      this.width = 0;                   // only used for type = IMG, TEXT, set to 0 until image loaded
      this.height = 0;                  //     "
      this.imgWidth = 0;                // user requested width in WC
      this.imgHeight = 0;               // user requested height in WC
      this.imgLorgX = 0;                // only used for type = IMG, TEXT, set to 0 until image loaded
      this.imgLorgY = 0;                //     "
      this.lorg = 1;                    // used by IMG and TEXT to set drawing origin
      // properties set by setStyleProperty method, if undefined render uses Cango default
      this.border = false;              // true = stroke outline with strokeColor & lineWidth
      this.strokeCol = null;            // render will stroke a path or border in this color
      this.lineWidthWC = null;          // border width world coords
      this.lineWidth = null;            // border width pixels
      this.lineCap = null;              // round, butt or square
      this.lineJoin = null;             // bevel, round, or miter
      this.savScale = 1;                // save accumulated scale factors for lineWidth of border
      // drop shadow properties
      this.shadowOffsetX = 0;
      this.shadowOffsetY = 0;
      this.shadowBlur = 0;
      this.shadowColor = "#000000";
      // dashed line properties
      this.dashed = [];
      this.dashOffset = 0;

      for (const prop in opt)
      {
        if (opt[prop] !== undefined) // own property, not inherited from prototype
        {
          setPropertyFn.call(this, prop, opt[prop]);
        }
      }
    }

    setDescriptor(imgData)
    {
      if (typeof imgData === "string")
      {
        this.imgBuf = new Image();    // pointer to the Image object when image is loaded
        this.imgBuf.src = imgData;    // start loading the image immediately
        return;
      }
      if ((imgData instanceof Image)||(imgData instanceof HTMLCanvasElement))
      {
        this.imgBuf = imgData;
        return;
      }
      console.warn("Type Error: Img descriptor");
    }

    dup()
    {
      const newObj = new Img(this.imgBuf);   // just copy reference
      dupCommon(newObj, this);

      newObj.srcX = this.srcX;
      newObj.srcY = this.srcY;
      newObj.srcWid = this.srcWid;
      newObj.srcHgt = this.srcHgt;
      newObj.width = this.width;
      newObj.height = this.height;
      newObj.imgWidth = this.imgWidth;
      newObj.imgHeight = this.imgHeight;
      newObj.imgLorgX = this.imgLorgX;
      newObj.imgLorgY = this.imgLorgY;
      newObj.lorg = this.lorg;
      // The other properties are dynamic, calculated at render

      return newObj;         // return a object which inherits Obj2D properties
    }
  
    crop(sx=0, sy=0, sWid=0, sHgt=0)
    {
      const croppedImg = new Img(this.imgBuf);

      croppedImg.srcX = sx;
      croppedImg.srcY = sy;
      croppedImg.srcWid = sWid;  
      croppedImg.srcHgt = sHgt;

      return croppedImg;
    }

    paintImg(gc)
    {
      if (!this.orgXscl) 
      {
        this.orgXscl = gc.xscl;
      } 
      const wcAspectRatio = Math.abs(gc.yscl/gc.xscl);
      let wid, hgt, 
          dx = 0,
          dy = 0;

      this.iso = true;   // over-ride any iso=false (rotation fails with no-iso pics)
      if (!this.imgBuf.width)
      {
        console.warn("Error: in image onload handler yet image NOT loaded!");
        return;
      }
      // setup the crop dimension if any
      const crpX = (this.srcX > 0)? Math.min(this.srcX, this.imgBuf.width-this.srcWid): 0;
      const crpY = (this.srcY > 0)? Math.min(this.srcY, this.imgBuf.height-this.srcHgt): 0;
      const crpWid = (this.srcWid > 0)? Math.min(this.imgBuf.width - crpX, this.srcWid): this.imgBuf.width;
      const crpHgt = (this.srcHgt > 0)? Math.min(this.imgBuf.height - crpY, this.srcHgt): this.imgBuf.height; 
      this.srcX = crpX;
      this.srcY = crpY;
      this.srcWid = crpWid;
      this.srcHgt = crpHgt;

      if (this.imgWidth && this.imgHeight)
      {
        wid = this.imgWidth;
        hgt = this.imgHeight*wcAspectRatio;
      }
      else if (this.imgWidth && !this.imgHeight)  // width only passed height is auto
      {
        wid = this.imgWidth;
        hgt = wid*this.srcHgt/this.srcWid;        // keep aspect ratio, use x units
      }
      else if (this.imgHeight && !this.imgWidth)  // height only passed width is auto
      {
        hgt = this.imgHeight*wcAspectRatio;
        wid = hgt*this.srcWid/this.srcHgt;        // keep aspect ratio
      }
      else    // no width or height default to natural size;
      {
        wid = this.srcWid/this.orgXscl;     // default to natural width if none passed
        hgt = wid*this.srcHgt/this.srcWid;  // keep aspect ratio, use x units
      }

      const wid2 = wid/2;
      const hgt2 = hgt/2;
      const lorgWC = [0, [0,    0], [wid2,    0], [wid,    0],
                         [0, hgt2], [wid2, hgt2], [wid, hgt2],
                         [0,  hgt], [wid2,  hgt], [wid,  hgt]];
      if (lorgWC[this.lorg] !== undefined)
      {
        dx = -lorgWC[this.lorg][0];
        dy = -lorgWC[this.lorg][1];
      }
      this.imgLorgX = dx;     // world coords offset to drawing origin
      this.imgLorgY = dy;
      this.width = wid;       // default to natural width if none passed
      this.height = hgt;      // default to natural height if none passed
      // construct the draw cmds for the Img bounding box
      const ulx = dx;
      const uly = dy;
      const llx = dx;
      const lly = dy+hgt;
      const lrx = dx+wid;
      const lry = dy+hgt;
      const urx = dx+wid;
      const ury = dy;
      const cmdsAry = "M"+ulx+" "+uly+" L"+llx+" "+lly+" "+lrx+" "+lry+" "+urx+" "+ury+" Z";
      this.pthCmds.p2dWC = new Path2D(cmdsAry);
      this.pthCmds.length = cmdsAry.length;
  
      // should only be called after image has been loaded into imgBuf
      const img = this.imgBuf;  // this is the place the image is stored in object
  
      gc.ctx.save();   // save raw pixels context, default styles no dropShadow
      gc.ctx.setTransform(this.netTfm.a, this.netTfm.b, this.netTfm.c, this.netTfm.d, this.netTfm.e, this.netTfm.f);
  
      gc.dropShadow(this);  // set up dropShadow if any
      // now insert the image canvas ctx will apply transforms (width etc in WC)
      gc.ctx.drawImage(img, this.srcX, this.srcY, this.srcWid, this.srcHgt, this.imgLorgX, this.imgLorgY, this.width, this.height);
      if (this.border)
      {
        gc.dropShadow(); // clear dropShadow, dont apply to the border (it will be on top of fill)
        // create the path to stroke with transforms applied to Path2D, not to canvas, else lineWidth scales non-iso!
        this.pthCmds.p2dPX = new Path2D();
        this.pthCmds.p2dPX.addPath(this.pthCmds.p2dWC, this.netTfm);
        gc.ctx.restore();   // revert to raw pixels ready to stroke border
        gc.ctx.save();      // save context with default styles 
        const col = this.strokeCol || gc.strokeColDef;
        let stkCol = col;
        if (col instanceof LinearGradient)
        {
          stkCol = gc.genLinGradPX(col, this);
        }
        else if (col instanceof RadialGradient)
        {
          stkCol = gc.genRadGradPX(col, this);
        }
        if (!this.orgXscl) this.orgXscl = gc.xscl;
        const zmScl = gc.xscl/this.orgXscl;
        if (this.lineWidthWC)
        {
          gc.ctx.lineWidth = this.lineWidthWC*this.savScale*gc.xscl;   // lineWidth in world coords so scale to px
        }
        else
        {
          gc.ctx.lineWidth = this.lineWidth*zmScl || gc.lineWidthDef*zmScl; 
        }
        gc.ctx.strokeStyle = stkCol;
        // if properties are undefined use Cango default
        gc.ctx.lineCap = this.lineCap || gc.lineCapDef;
        gc.ctx.lineJoin = this.lineJoin || gc.lineJoinDef;
        gc.ctx.stroke(this.pthCmds.p2dPX);
      }
      gc.ctx.restore();     // back to raw pixels and default styles

      if (this.dragNdrop !== null)
      {
        initDragAndDrop(gc);
        gc.handleDnD(this);
      }
    }
  
    paint(gc)
    {
      const imgLoaded = ()=>{ 
        this.paintImg(gc);
      }

      if (this.imgBuf.complete || this.imgBuf instanceof HTMLCanvasElement)    // see if already loaded
      {
        imgLoaded();
      }
      else
      {
        this.imgBuf.addEventListener('load', imgLoaded);
      }
    }
  } 

  Text = class extends Obj2D
  {
    constructor (txtString, opt = {})
    {
      super();
      this.type = "TEXT";               // type string to instruct the render method
      this.txtStr = "";                 // store the text String
      this.pthCmds = new Path2DObj();   // Path2D that draws the text bounding box
      this.width = 0;                   // only used for type = IMG, TEXT, set to 0 until image loaded
      this.height = 0;                  //     "
      this.imgLorgX = 0;                //     "
      this.imgLorgY = 0;                //     "
      this.lorg = 1;                    // used by IMG and TEXT to set drawing origin
      // properties set by setStyleProperty method, if undefined render uses Cango default
      this.border = false;              // true = stroke outline with strokeColor & lineWidth
      this.fillCol = null;              // only used if type == SHAPE or TEXT
      this.bgFillColor = null;          // only used if type = TEXT
      this.strokeCol = null;            // render will stroke a border in this color
      this.fontSize = null;             // fontSize in pixels (TEXT only)
      this.fontSizeWC = null;           // fontSize in world coords (TEXT only)
      this.fontWeight = null;           // fontWeight 100..900 (TEXT only)
      this.fontFamily = null;           // (TEXT only)
      this.lineWidthWC = null;          // border width world coords
      this.lineWidth = null;            // border width pixels
      this.lineCap = null;              // round, butt or square
      this.lineJoin = null;             // bevel, round or miter
      this.savScale = 1;                // save accumulated scale factors to scale lineWidth of border 
      // drop shadow properties
      this.shadowOffsetX = 0;
      this.shadowOffsetY = 0;
      this.shadowBlur = 0;
      this.shadowColor = "#000000";
      // dashed line properties
      this.dashed = [];
      this.dashOffset = 0;

      this.setDescriptor(txtString);

      for (const prop in opt)
      {
        if (opt[prop] !== undefined)   // own property, not inherited from prototype
        {
          setPropertyFn.call(this, prop, opt[prop]);
        }
      }
    }

    setDescriptor(str)
    {
      if (typeof str !== "string")
      {
        console.warn("Type Error: Text descriptor");
        return;
      }
      this.txtStr = str;
    }

    dup()
    {
      const newObj = new Text(this.txtStr.slice(0));
      dupCommon(newObj, this)

      newObj.bgFillColor = this.bgFillColor;
      newObj.width = this.width;
      newObj.height = this.height;
      newObj.imgLorgX = this.imgLorgX;
      newObj.imgLorgY = this.imgLorgY;
      newObj.lorg = this.lorg;
      newObj.fontSize = this.fontSize;
      newObj.fontSizeWC = this.fontSizeWC;
      newObj.fontWeight = this.fontWeight;
      newObj.fontFamily = this.fontFamily;
      // The other properties are dynamic, calculated at render

      return newObj;
    }

    paint(gc)
    {
      const fntFm = this.fontFamily || gc.fontFamilyDef,
            fntWt = this.fontWeight || gc.fontWeightDef,
            lorg = this.lorg || 1;
      let fntSz,      // font size in pixels, Note: char cell is ~1.4*fontSize pixels high
          dx = 0,
          dy = 0;

          // support for zoom and pan
      const zmScl = gc.xscl/gc.savWCscl.xscl;   // scale for any zoom factor
      if (this.fontSizeWC)
      {
        fntSz = this.fontSizeWC*gc.savWCscl.xscl;   // fontSize in world coords so scale to px
      }
      else
      {
        fntSz = this.fontSize || gc.fontSizeDef 
      }
      // set the drawing context to measure the size
      gc.ctx.save();
      gc.ctx.resetTransform();  // reset to identity matrix
      gc.ctx.font = fntWt+" "+fntSz*zmScl+"px "+fntFm;
      const wid = gc.ctx.measureText(this.txtStr).width;  // width in pixels
      gc.ctx.restore();
      // keep in pixel dimensions (Img and Text are drawn in px dimensions, avoiding font size rounding) 
      const hgt = fntSz*zmScl;    // TEXT height from bottom of decender to top of capitals
      const wid2 = wid/2;
      const hgt2 = hgt/2;
      const lorgWC = [[0, 0], [0,  hgt], [wid2,  hgt], [wid,  hgt],
                              [0, hgt2], [wid2, hgt2], [wid, hgt2],
                              [0,    0], [wid2,    0], [wid,    0]];
      if (lorgWC[lorg] !== undefined)
      {
        dx = -lorgWC[lorg][0];
        dy = lorgWC[lorg][1];
      }
      this.imgLorgX = dx;           // pixel offsets to drawing origin
      this.imgLorgY = dy-0.25*hgt;  // correct for alphabetic baseline, its offset about 0.25*char height

      // construct the cmdsAry for the text bounding box (world coords)
      const ulx = dx;
      const uly = dy;
      const llx = dx;
      const lly = dy-hgt;
      const lrx = dx+wid;
      const lry = dy-hgt;
      const urx = dx+wid;
      const ury = dy;
      const cmdsAry = "M"+ulx+" "+uly+" L"+llx+" "+lly+" "+lrx+" "+lry+" "+urx+" "+ury+" Z";
      this.pthCmds.p2dWC = new Path2D(cmdsAry);
      this.pthCmds.length = cmdsAry.length;    // used for warning if length == 0
      // set up the fill and stroke colors, gradients will be rendered in world coords 
      let col = this.strokeCol || gc.strokeColDef;
      let stkCol = col;
      if (col instanceof LinearGradient)
      {
        stkCol = gc.genLinGradWC(col);
      }
      else if (col instanceof RadialGradient)
      {
        stkCol = gc.genRadGradWC(col); 
      }
  
      col = this.fillCol || gc.fillColDef;
      let filCol = col;
      if (col instanceof LinearGradient)
      {
        filCol = gc.genLinGradWC(col);
      }
      else if (col instanceof RadialGradient)
      {
        filCol = gc.genRadGradWC(col); 
      }
  
      let bkgCol;
      if (this.bgFillColor)  // leave bkg = undefined if no bgFillColor set
      {
        col = this.bgFillColor;
        if (typeof col === "string")
        {
          bkgCol = this.bgFillColor;
        }
        else if (col instanceof LinearGradient)
        {
          bkgCol = gc.genLinGradWC(col);
        }
        else if (col instanceof RadialGradient)
        {
          bkgCol = gc.genRadGradWC(col); 
        }
      }
    
      gc.ctx.save();   // save raw canvas no transforms no dropShadow
      gc.ctx.setTransform(this.netTfm.a, this.netTfm.b, this.netTfm.c, this.netTfm.d, this.netTfm.e, this.netTfm.f);
      // if a bgFillColor is specified then fill the bounding box before rendering the text
      if (bkgCol)
      {
        // create the bounding box path
        gc.ctx.save();
        gc.ctx.fillStyle = bkgCol;
        gc.ctx.strokeStyle = bkgCol;
        gc.ctx.lineWidth = 0.10*fntSz;  // expand by 5% (10% width gives 5% outside outline)
        gc.ctx.fill(this.pthCmds.p2dWC);
        gc.ctx.stroke(this.pthCmds.p2dWC); // stroke the outline
  
        gc.ctx.restore();
      }
      // now draw the text in world coords
      gc.ctx.font = fntWt+" "+hgt+"px "+fntFm;

      gc.ctx.fillStyle = filCol;
      gc.ctx.fillText(this.txtStr, this.imgLorgX, this.imgLorgY); // imgLorgX,Y are in pixels for text
      if (this.border)
      {
        gc.dropShadow(); // clear dropShadow, dont apply to the border (it will be on top of fill)
        // support for zoom and pan changing lineWidth
        if (this.lineWidthWC)
        {
          gc.ctx.lineWidth = this.lineWidthWC*gc.xscl*zmScl;
        }
        else
        {
          gc.ctx.lineWidth = this.lineWidth*zmScl || gc.lineWidthDef*zmScl;
        }
        // if properties are undefined use Cango default
        gc.ctx.strokeStyle = stkCol;
        gc.ctx.lineCap = this.lineCap || gc.lineCapDef;
        gc.ctx.lineJoin = this.lineJoin || gc.lineJoinDef;
        gc.ctx.strokeText(this.txtStr, this.imgLorgX, this.imgLorgY);
      }
      gc.ctx.restore();  // back to raw pixels and default styles

      if (this.dragNdrop !== null)
      {
        initDragAndDrop(gc);
        gc.handleDnD(this);
      }
    }
  } 

  class Layer
  {
    constructor(canvasID, canvasElement)
    {
      this.id = canvasID;
      this.cElem = canvasElement;
      this.dragObjects = [];
    }
  }

  function getLayer(cgo)
  {
    let lyr = cgo.bkgCanvas.layers[0];

    for (let i=1; i < cgo.bkgCanvas.layers.length; i++)
    {
      if (cgo.bkgCanvas.layers[i].id === cgo.cId)
      {
        lyr = cgo.bkgCanvas.layers[i];
        break;
      }
    }
    return lyr;    // Layer object
  }

  Cango = class 
  {
    constructor(cvs)
    {
      const resizeLayers = ()=>
      {
        // every Cango instance on the bkgCanvas will call this handler, only need to fix things once
        const t = this.bkgCanvas.offsetTop + this.bkgCanvas.clientTop,
              l = this.bkgCanvas.offsetLeft + this.bkgCanvas.clientLeft,
              w = this.bkgCanvas.offsetWidth,
              h = this.bkgCanvas.offsetHeight;

        // check if canvas is resized when window -resized, allow some rounding error in layout calcs
        if ((Math.abs(w - this.rawWidth)/w < 0.01) && (Math.abs(h - this.rawHeight)/h < 0.01))
        {
          // canvas size didn't change (or has already been resized already) so return
          return;
        }
        // canvas has been resized so re-size all the overlay canvases
        // kill off any animations on resize (else they still contiune along with any new ones)
        if (this.bkgCanvas.timeline && this.bkgCanvas.timeline.animTasks.length) // this is only called once
        {
          this.deleteAllAnimations();
        }
        // fix all Cango contexts to know about new size
        this.rawWidth = w;
        this.rawHeight = h;
        this.aRatio = w/h;
        // now every Cango instance has the new size (but their canvas haven't heard yet)
        // there may be multiple Cango contexts a layer, so this resize may be called multiple times
        if (this.cnvs.width == w && this.cnvs.height == h) // canvas already fixed so return
        {
          return;
        }
        this.bkgCanvas.width = w;    // reset canvas pixels width
        this.bkgCanvas.height = h;   // don't use style for this, all drawing will be erased
        // step through the stack of canvases (if any)
        for (let j=1; j<this.bkgCanvas.layers.length; j++)  // bkg is layer[0]
        {
          const ovl = this.bkgCanvas.layers[j].cElem;
          if (ovl)
          {
            ovl.style.top = t+'px';
            ovl.style.left = l+'px';
            ovl.style.width = w+'px';
            ovl.style.height = h+'px';
            ovl.width = w;    // reset canvas attribute to pixel width
            ovl.height = h;  
          }
        }
        // if zoom pan is enabled reset it
        if (this.bkgCanvas.zNp)
        {
          this.bkgCanvas.zNp.drawZnPcontrols();
          this.bkgCanvas.zNp.resize(w, h);
        }
      }

      if ((typeof cvs === "string") && document.getElementById(cvs))   // element ID was passed
      {
        this.cnvs = document.getElementById(cvs);
        this.cId = cvs;
        if (!(this.cnvs instanceof HTMLCanvasElement))  // not a canvas
        {
          console.warn("Type Error: Cango constructor argument not an HTMLCanvasElement");
          return;
        }
        // check if this is a context for an overlay
        if (this.cId.indexOf("_ovl_") !== -1)
        {
          this.cgoType = "OVL"; 
          // this is an overlay. get a reference to the backGround canvas
          const bkgId = this.cId.slice(0, this.cId.indexOf("_ovl_"));
          this.bkgCanvas = document.getElementById(bkgId);
        }
        else
        {
          this.cgoType = "BKG"; 
          this.bkgCanvas = this.cnvs;
        }
        this.rawWidth = this.cnvs.offsetWidth;    // ignore attribute, use the on screen pixel size
        this.rawHeight = this.cnvs.offsetHeight;
        if (this.bkgCanvas.unique === undefined)
        {
          this.bkgCanvas.unique = 0;
        }    
      }
      else if (cvs instanceof HTMLCanvasElement)   // canvas element passed
      {
        this.cnvs = cvs;
        this.bkgCanvas = this.cnvs;
        this.rawWidth = this.cnvs.width;
        this.rawHeight = this.cnvs.height;
        if (!this.bkgCanvas.unique === undefined)
        {
          this.bkgCanvas.unique = 0;
        }    
        if (document.contains(cvs))  // element is part of the DOM
        {
          this.cId = this.cnvs.id;
          this.cgoType = "BKG"; 
          if (!this.cId)
          {
            this.cId = "_bkg_"+this.getUnique();
            this.cnvs.id = this.cId;    // set the attribute to match new id
          }
        }
        else  // off-screen canvas
        {
          this.cId = "_os_"+this.getUnique();  // over-ride any existing id
          this.cgoType = "OS";     
        }
      }
      else  // not a canvas element
      {
        console.warn("Type Error: Cango constructor argument 1");
        return;
      }

      this.aRatio = this.rawWidth/this.rawHeight;
      this.widthPW = 100;                 // width of canvas in Percent Width coords
      this.heightPW = 100/this.aRatio;    // height of canvas in Percent Width coords
      if (this.bkgCanvas.layers === undefined)
      {
        // create an array to hold all the overlay canvases for this canvas
        this.bkgCanvas.layers = [];
        // make a Layer object for the bkgCanvas
        const bkgL = new Layer(this.cId, this.cnvs);
        this.bkgCanvas.layers[0] = bkgL;
        // make sure the overlay canvases always match the bkgCanvas size
        if (this.cgoType !== "OS")
        {
          addEventListener("resize", resizeLayers);
        }
      }
      if (this.cnvs.resized === undefined)
      {
        // make canvas native aspect ratio equal style box aspect ratio.
        // Note: rawWidth and rawHeight are floats, assignment to ints will truncate
        this.cnvs.width = this.rawWidth;          // reset canvas pixels width
        this.cnvs.height = this.rawHeight;        // don't use style for this
        this.cnvs.resized = true;
      }
      this.ctx = this.cnvs.getContext('2d');      // draw direct to screen canvas
      this.vpW = this.rawWidth;                   // gridbox width in pixels (no gridbox, use full canvas)
      this.vpH = this.rawHeight;                  // gridbox height in pixels, canvas height = width/aspect ratio
      this.vpOrgX = 0;                            // gridbox origin in pixels (upper left for SVG, the default)
      this.vpOrgYsvg = 0;                         // save vpOrgY, needed when switching between RHC and SVG and back
      this.vpOrgYrhc = this.rawHeight;            //   "
      this.vpOrgY = this.vpOrgYsvg;               // gridbox origin in pixels (upper left for SVG, the default)
      this.vpOrgXWC = this.vpOrgX;                // gridbox origin in world coords (upper left for SVG, the default)
      this.vpOrgYWC = this.vpOrgYsvg              //   ""
      this.vpWWC = this.vpW;                      // gridbox width in world coords (default use pixels) 
      this.vpHWC = this.vpH;                      // gridbox height in world coords (default use pixels)
      this.xscl = 1.0;                            // world x axis scale factor, default: pixels
      this.yscl = 1.0;                            // world y axis scale factor, +ve down (SVG style default)
      this.yDown = true;                          // set by setWordlCoordsRHC & setWorldCoordsSVG (SVG is default)
      this.isoYscl = this.xscl;                   // drawing is done with iso coords (updated prior to render)
      this.xoffset = 0;                           // world x origin offset from gridbox left in pixels
      this.yoffset = 0;                           // world y origin offset from gridbox bottom in pixels
      this.zNp = null;
      this.savWCscl = {xscl:this.xscl, yscl:this.yscl, xoffset:this.xoffset, yoffset:this.yoffset };     // save world coords for zoom/pan
      this.savGB = {lft: 0, bot: 0, spanX: 100, spanY: this.heightPW};
      this.ctx.textAlign = "left";                // all offsets are handled by lorg facility
      this.ctx.textBaseline = "alphabetic";
      this.strokeColDef = "rgba(0, 0, 0, 1.0)";   // black
      this.lineWidthDef = 1;                      // 1 pixel
      this.lineCapDef = "butt";
      this.lineJoinDef = "miter";
      this.fillColDef = "rgba(128,128,128,1.0)";  // gray
      this.fontSizeDef = 12;                      // pixels
      this.fontWeightDef = 400;                   // 100..900, 400 = normal, 700 = bold
      this.fontFamilyDef = "Consolas, Monaco, 'Andale Mono', monospace";
      this.clipCount = 0;                         // count ClipMask calls for use by resetClip

      this.setWorldCoordsSVG();                   // set default coordinate values (eqiv to raw pixels)
    }
  
    getUnique()
    {
      this.bkgCanvas.unique += 1; 
      return this.bkgCanvas.unique;
    }

    toPixelCoords(x, y)
    {
      // transform x,y in world coords to canvas pixel coords (top left is 0,0 y axis +ve down)
      const xPx = this.vpOrgX+this.xoffset+x*this.xscl,
            yPx = this.vpOrgY+this.yoffset+y*this.yscl;

      return {x: xPx, y: yPx};
    }

    toWorldCoords(xPx, yPx)
    {
      // transform xPx,yPx in raw canvas pixels to world coords (lower left is 0,0 +ve up)
      const xW = (xPx - this.vpOrgX - this.xoffset)/this.xscl,
            yW = (yPx - this.vpOrgY - this.yoffset)/this.yscl;

      return {x: xW, y: yW};
    }

    getCursorPosWC(evt)
    {
      // pass in any mouse event, returns the position of the cursor in raw pixel coords
      const rect = this.cnvs.getBoundingClientRect();

      return this.toWorldCoords(evt.clientX-rect.left, evt.clientY-rect.top);
    }

    clearCanvas(fillColor)
    {
      if (typeof(fillColor) == "string")
      {
        this.ctx.save();            // going to change fillStyle, save current
        this.ctx.fillStyle = fillColor;
        this.ctx.fillRect(0, 0, this.rawWidth, this.rawHeight);
        this.ctx.restore();
      }
      else
      {
        this.ctx.clearRect(0, 0, this.rawWidth, this.rawHeight);
      }
      // all drawing erased, but graphics contexts remain intact
      // clear the dragObjects array, draggables put back when rendered
      const layerObj = getLayer(this);
      layerObj.dragObjects.length = 0;
    }

    gridboxPadding(left, bottom, right, top)
    {
      // left, bottom, right, top are the padding from the respective sides, 
      // all are in % of canvas width units, negative values are set to 0.
      const setDefault = ()=>{
        this.vpW = this.rawWidth;
        this.vpH = this.rawHeight;
        this.vpOrgX = 0;
        this.vpOrgY = 0;
        this.setWorldCoordsSVG(); // if new gridbox created, world coords are garbage, so reset to defaults
      }

      if (left === undefined)   // no error just reset to default
      {
        setDefault();
        return;
      }
      // check if only left defined
      if (bottom === undefined)  // only one parameter
      {
        if ((left >= 50) || (left < 0))
        {
          console.warn("Range Error: gridboxPadding right less than left");
          setDefault();
          return;
        }
        bottom = left;
      }
      if ((left < 0) || (left > 99))
      {
        left = 0;
      }
      // now we have a valid left and a bottom
      if ((bottom < 0) || (bottom > 99/this.aRatio))
      {
        bottom = 0;
      }
      if (right === undefined)   // right == 0 is OK
      {
        right = left;
      }
      else if (right < 0)
      {
        right = 0;
      }
      if (top === undefined)    // top == 0 is OK
      {
        top = bottom;
      }
      else if (top < 0)
      {
        top = 0;
      }
      // now we have all 4 valid padding values
      const width = 100 - left - right;
      const height = 100/this.aRatio - top - bottom;
      if ((width < 0) || (height < 0))
      {
        console.warn("Range Error: gridboxPadding invalid dimensions");
        setDefault();
        return;
      }

      this.vpW = width*this.rawWidth/100;
      this.vpH = height*this.rawWidth/100;
      // now calc upper left of gridbox in pixels = this is the vpOrg
      this.vpOrgX = left*this.rawWidth/100;
      this.vpOrgYsvg = top*this.rawWidth/100;  // SVG vpOrg is up at the top left
      this.vpOrgYrhc = this.vpOrgYsvg+this.vpH;// RHC vpOrg is down at the lower left
      this.vpOrgY = this.vpOrgYsvg;            // SVG is the default
      this.savGB.lft = left;
      this.savGB.bot = bottom;
      this.savGB.spanX = width;
      this.savGB.spanY = height;
      this.setWorldCoordsSVG(); // if new gridbox created, world coords are garbage, so reset to defaults
    }

    setGridbox(left, bottom, spanX, spanY)
    {
      // left, bottom, spanX, spanY are all are in % of canvas width units,
      // negative values are set to 0.
      const setDefault = ()=>{
        this.vpW = this.rawWidth;
        this.vpH = this.rawHeight;
        this.vpOrgX = 0;
        this.vpOrgY = 0;
        this.setWorldCoordsSVG(); // if new gridbox created, world coords are garbage, so reset to defaults
      }

      if (arguments.length !== 4)
      {
        console.warn("Range Error: setGridbox invalid dimensions");
        setDefault();
        return;
      }
      // we have left, bottom, spanX and spany values
      if ((left < 0) || (left > 99))
      {
        console.warn("Range Error: setGridbox invalid left offset value");
        left = 0;
      }
      if ((bottom < 0) || (bottom > 99/this.aRatio))
      {
        console.warn("Range Error: setGridbox invalid bottom offset value");
        bottom = 0;
      }
      if (spanX < 1 || spanX > 100-left)
      {
        console.warn("Range Error: setGridbox invalid gridbox width value");
        spanX = 100-left;
      }
      if (spanY < 1 || spanY > 100/Math.floor(this.aRatio) - bottom)
      {
        console.warn("Range Error: setGridbox invalid gridbox height value");
        spanY = 100/this.aRatio - bottom;
      }
      const top = 100/this.aRatio - spanY - bottom;

      this.vpW = spanX*this.rawWidth/100;
      this.vpH = spanY*this.rawWidth/100;
      // now calc upper left of gridbox in pixels = this is the vpOrg
      this.vpOrgX = left*this.rawWidth/100;
      this.vpOrgYsvg = top*this.rawWidth/100;  // SVG vpOrg is up at the top left
      this.vpOrgYrhc = this.vpOrgYsvg+this.vpH;// RHC vpOrg is down at the lower left
      this.vpOrgY = this.vpOrgYsvg;            // SVG is the default
      this.savGB.lft = left;
      this.savGB.bot = bottom;
      this.savGB.spanX = spanX;
      this.savGB.spanY = spanY;
      this.setWorldCoordsSVG(); // if new gridbox created, world coords are garbage, so reset to defaults
    }

    fillGridbox(fillColor)
    {
      // Note: Shape descriptors (SVG) assume iso x and y coords so convert Yspan to isoWC
      const isoWC_to_yWC = Math.abs(this.yscl/this.xscl);
      const gbData = "M"+this.vpOrgXWC+","+this.vpOrgYWC*isoWC_to_yWC+" h"+this.vpWWC+" v"+this.vpHWC*isoWC_to_yWC+" h-"+this.vpWWC+" z";
      this.drawShape(gbData, {fillColor:fillColor});
    }

    setWorldCoordsSVG(vpOrgXWC=0, vpOrgYWC=0, spanXWC=0, spanYWC=0)
    {
      // gridbox origin is upper left
      this.vpOrgXWC = vpOrgXWC;
      this.vpOrgYWC = vpOrgYWC;
      this.vpWWC = spanXWC;
      this.vpHWC = spanYWC;

      this.vpOrgY = this.vpOrgYsvg;       // switch vpOrg to upper left corner of gridbox
      if (spanXWC > 0)
      {
        this.xscl = this.vpW/spanXWC;
      }
      else
      {
        this.xscl = 1;                    // use pixel units
        this.vpWWC = this.vpW;
      }
      if (spanYWC > 0)
      {
        this.yscl = this.vpH/spanYWC;       // yscl is positive for SVG
      }
      else
      {
        this.yscl = this.xscl;            // square pixels
        this.vpHWC = this.vpH/this.xscl;
      }
      this.yDown = true;                  // flag true for SVG world coords being used
      this.isoYscl = this.xscl;
      this.xoffset = -vpOrgXWC*this.xscl;
      this.yoffset = -vpOrgYWC*this.yscl;   // reference to upper left of gridbox
      // save values to support resetting zoom and pan
      this.savWCscl.xscl = this.xscl;
      this.savWCscl.yscl = this.yscl;
      this.savWCscl.xoffset = this.xoffset;
      this.savWCscl.yoffset = this.yoffset;
    }

    setWorldCoordsRHC(vpOrgXWC=0, vpOrgYWC=0, spanXWC=0, spanYWC=0)
    {
      this.vpOrgXWC = vpOrgXWC;
      this.vpOrgYWC = vpOrgYWC;
      this.vpWWC = spanXWC;
      this.vpHWC = spanYWC;

      this.vpOrgY = this.vpOrgYrhc;   // switch vpOrg to lower left corner of gridbox
      if (spanXWC > 0)
      {
        this.xscl = this.vpW/spanXWC;
      }
      else
      {
        this.xscl = 1;                   // use pixel units
        this.vpWWC = this.vpW;
      }
      if (spanYWC > 0)
      {
        this.yscl = -this.vpH/spanYWC;    // yscl is negative for RHC
      }
      else
      {
        this.yscl = -this.xscl;          // square pixels
        this.vpHWC = this.vpH/this.xscl;
      }
      this.yDown = false;             // flag false for RHC world coords
      this.isoYscl = -this.xscl;
      this.xoffset = -vpOrgXWC*this.xscl;
      this.yoffset = -vpOrgYWC*this.yscl;
      // save these values to support resetting zoom and pan
      this.savWCscl.xscl = this.xscl;
      this.savWCscl.yscl = this.yscl;
      this.savWCscl.xoffset = this.xoffset;
      this.savWCscl.yoffset = this.yoffset;
    }

    setPropertyDefault(propertyName, value)
    {
      if ((typeof propertyName !== "string")||(value === undefined)||(value === null))
      {
        return;
      }
      switch (propertyName.toLowerCase())
      {
        case "fillcolor":
          if ((typeof value === "string")||(typeof value === "object"))  // gradient will be an object
          {
            this.fillColDef = value;
          }
          break;
        case "strokecolor":
          if ((typeof value === "string")||(typeof value === "object"))  // gradient will be an object
          {
            this.strokeColDef = value;
          }
          break;
        case "linewidth":
        case "strokewidth":
          this.lineWidthDef = value;
          break;
        case "linecap":
          if ((typeof value === "string")&&((value === "butt")||(value ==="round")||(value === "square")))
          {
            this.lineCapDef = value;
          }
          break;
        case "linejoin":
          if ((typeof value === "string")&&((value === "bevel")||(value ==="round")||(value === "miter")))
          {
            this.lineJoinDef = value;
          }
          break;
          case "fontfamily":
          if (typeof value === "string")
          {
            this.fontFamilyDef = value;
          }
          break;
        case "fontsize":
          this.fontSizeDef = value;
          break;
        case "fontweight":
          if ((typeof value === "string")||((value >= 100)&&(value <= 900)))
          {
            this.fontWeightDef = value;
          }
          break;
        default:
          break;
      }
    }

    dropShadow(obj)  // no argument will reset to no drop shadows 
    {
      let xOfs = 0,
          yOfs = 0,
          radius = 0,
          color = "#000000",
          yScale = 1;

      if (obj != undefined)
      {
        xOfs = obj.shadowOffsetX || 0;
        yOfs = obj.shadowOffsetY || 0;
        radius = obj.shadowBlur || 0;
        color = obj.shadowColor || "#000000";
        yScale = (obj.iso)? this.isoYscl: this.yscl;   // iso scaling
      }
      this.ctx.shadowOffsetX = xOfs*this.xscl;
      this.ctx.shadowOffsetY = yOfs*yScale;
      this.ctx.shadowBlur = radius*this.xscl;
      this.ctx.shadowColor = color;
    }

    genOfsTfmMatrix(obj)
    {
      const yWC_to_isoWC = Math.abs(this.yscl/this.xscl);
      let ofsMat = matrixIdent();

      ofsMat = matrixMult(obj.ofsTfmMat, ofsMat);   // ofsTfmMat will be identity unless transformRestore called

      obj.ofsTfmAry.slice().forEach((xfmr)=>{
          if (xfmr.type === "TRN")
        {
          // objects descriptors assume iso world coords 
          ofsMat = matrixTranslate(ofsMat, xfmr.args[0], xfmr.args[1]*yWC_to_isoWC); 
        }
        else if (xfmr.type === "ROT")
        {
          ofsMat = matrixRotate(ofsMat, -xfmr.args[0]);
        }
        else if (xfmr.type === "SCL")
        {
          obj.savScale *= Math.abs(xfmr.args[0]); // accumulate scaling to apply to lineWidth
          ofsMat = matrixScale(ofsMat, xfmr.args[0], xfmr.args[1]);
        }
        else if (xfmr.type === "SKW")
        {
          ofsMat = matrixSkew(ofsMat, -xfmr.args[0], xfmr.args[1]);
        } 
      });

      return ofsMat;
    }

    genNetTfmMatrix(obj, softTfm)
    {
      const yWC_to_isoWC = Math.abs(this.yscl/this.xscl);

      obj.netTfm = matrixIdent();  // clear out previous transforms

    // handle world coordinate scaling, assuming default is iso
    if (!obj.iso)
      { 
        // SVG coords descriptors assume iso scaling, Cango allows non-iso
        obj.netTfm = matrixScale(obj.netTfm, 1, yWC_to_isoWC); 
      }
      if (obj.type === "IMG" && !this.yDown)
      {
        // Img always upright and iso
        obj.netTfm = matrixScale(obj.netTfm, 1, -1);
      }
      else if (obj.type === "TEXT")
      {
        obj.netTfm = matrixScale(obj.netTfm, 1/this.xscl, 1/this.isoYscl);
      }
    
      obj.hardTfmAry.slice(0).forEach((xfmr)=>{
          if (xfmr.type === "TRN")
        {
          // objects descriptors assume iso world coords 
          obj.netTfm = matrixTranslate(obj.netTfm, xfmr.args[0], xfmr.args[1]*yWC_to_isoWC); 
        }
        else if (xfmr.type === "ROT")
        {
          obj.netTfm = matrixRotate(obj.netTfm, -xfmr.args[0]);
        }
        else if (xfmr.type === "SCL")
        {
          obj.savScale *= Math.abs(xfmr.args[0]); // accumulate scaling to apply to lineWidth
          obj.netTfm = matrixScale(obj.netTfm, xfmr.args[0], xfmr.args[1]);
        }
        else if (xfmr.type === "SKW")
        { 
          obj.netTfm = matrixSkew(obj.netTfm, -xfmr.args[0], xfmr.args[1]);    
        }
      });

      obj.netTfm = matrixMult(softTfm, obj.netTfm);

      // canvas ctx expects transforms in reverse order (matricies use preMultiply)
      obj.netTfm = matrixScale(obj.netTfm, this.xscl, this.isoYscl);
      obj.netTfm = matrixTranslate(obj.netTfm, this.vpOrgX + this.xoffset, this.vpOrgY + this.yoffset);
  
      }

    handleDnD(obj)
    {
      // update dragNdrop layer to match this canvas
      const currLr = getLayer(this);
      if (currLr !== obj.dragNdrop.layer)
      {
        if (obj.dragNdrop.layer)  // if not the first time rendered
        {
          // remove the object reference from the old layer
          const aidx = obj.dragNdrop.layer.dragObjects.indexOf(obj);
          if (aidx !== -1)
          {
            obj.dragNdrop.layer.dragObjects.splice(aidx, 1);
          }
        }
      }
      obj.dragNdrop.cgo = this;
      obj.dragNdrop.layer = currLr;
      // now push it into Cango.dragObjects array, its checked by canvas mousedown event handler
      if (!obj.dragNdrop.layer.dragObjects.includes(obj))
      {
        obj.dragNdrop.layer.dragObjects.push(obj);
      }
    }
  
   /*========================================================
    * render will draw a Group or Obj2D.
    * If an Obj2D is passed, update the netTfm and render it.
    * If a Group is passed, recursively update the netTfm of 
    * the group's family tree, then render all Obj2Ds.
    *-------------------------------------------------------*/
    render(rootObj, clear)
    {
      const yWC_to_isoWC = Math.abs(this.xscl/this.yscl);
      this.isoYscl = (this.yDown)? this.xscl: -this.xscl;  // update to the latest in case of zoom etc changing WC

      const handleTransforms = (obj)=>
      {
        const grpTfmMat = (obj.parent)? matrixClone(obj.parent.netTfmMat): matrixIdent();
        obj.savScale = (obj.parent)? obj.savScale: 1;  // reset the scale factor for re-calc
        // generate the currOfsTfmMat
        obj.ofsTfmMat = this.genOfsTfmMatrix(obj);
        // finished with ofsTfmAry reset it 
        obj.ofsTfmAry.length = 0;
        // save the matrix for transformRestore
        obj.currOfsTfmMat = matrixClone(obj.ofsTfmMat);
        let softTfmMat = matrixMult(grpTfmMat, obj.ofsTfmMat);

        // finished with ofsTfmMat so reset it
        obj.ofsTfmMat = matrixIdent();
        // apply the soft transforms to the dwgOrg of the Group or the Obj2D
        obj.dwgOrg = matrixTransformPoint(softTfmMat, {x:0, y:0});
        obj.dwgOrg.y *= yWC_to_isoWC;
      
        if (obj.type === "GRP")
        {
          obj.netTfmMat = softTfmMat;
        }
        else
        {
          this.genNetTfmMatrix(obj, softTfmMat);
        }
      }

      const recursiveGenNetTfmAry = (root)=>
      {
        const flatAry = [];

        const iterate = (obj)=>
        {
          if (obj.type === "GRP")    // find Obj2Ds to draw
          {
            if (typeof obj.preRender === "function")
            {
              obj.preRender(this);    // user defined object (extends Group) pre-render code
            }

            handleTransforms(obj);
            obj.children.forEach((childNode)=>{
              iterate(childNode);
            });
            flatAry.push(new ClipMask());   // clear mask at the end of each grp children render
          }
          else
          {
            handleTransforms(obj);
            flatAry.push(obj);       // just push into the array to be drawn
          }
        }
        // now propagate the current grpXfm through the tree of children
        iterate(root);

        return flatAry;
      }

  // ============ Start Here =====================================================

      if (!types.includes(rootObj.type))
      {
        console.warn("Type Error: render argument 1");
        return;
      }
      // recursively apply transforms returning the family tree flattened to an array of Obj2D
      const objAry = recursiveGenNetTfmAry(rootObj);
      const renderInSeries = async ()=>
      { 
        const jobList = [];
        for (let j=0; j<objAry.length; j++)
        {
          const obj = objAry[j];
          if (obj.type === "IMG")
          {
            await new Promise(resolve =>{
              const imgLoaded = ()=>{ 
                jobList.push(obj)
                resolve();
              }
              if (obj.imgBuf.complete || obj.imgBuf instanceof HTMLCanvasElement)    // see if already loaded
              {
                imgLoaded();
              }
              else
              {
                obj.imgBuf.addEventListener('load', imgLoaded);
              }
            });
          }
          else
          {
            jobList.push(obj);          
          } 
        }

        if (clear === true || clear === "clear")
        {
          this.clearCanvas();
        }
        for (let j=0; j<jobList.length; j++)
        {
          jobList[j].paint(this);
        }
      }
      // now render the array of Obj2Ds in series
      renderInSeries();
    }

    genLinGradPX(lgrad, obj)
    {
      const p1x = lgrad.grad.x1,
            p1y = lgrad.grad.y1,
            p2x = lgrad.grad.x2,
            p2y = lgrad.grad.y2;
      let tp1 = matrixTransformPoint(obj.netTfm, {x:p1x, y:p1y});
      let tp2 = matrixTransformPoint(obj.netTfm, {x:p2x, y:p2y});
      if (obj.type === "IMG" && !this.yDown)    // IMG is flipped vertically, don't flip the gradient
      {
        const m = matrixScale(obj.netTfm, 1, -1);  // flip vertically
        tp1 = matrixTransformPoint(obj.netTfm, {x:p1x, y:-p1y});
        tp2 = matrixTransformPoint(obj.netTfm, {x:p2x, y:-p2y});
      }

      const grad = this.ctx.createLinearGradient(tp1.x, tp1.y, tp2.x, tp2.y);
      lgrad.colorStops.forEach((colStop)=>{
        grad.addColorStop(colStop.stop, colStop.color);
      });

      return grad;
    }

    genRadGradPX(rgrad, obj)
    {
      const scl = obj.savScale*this.xscl;
      const p1x = rgrad.grad.x1,
            p1y = rgrad.grad.y1,
            r1 = rgrad.grad.r1*scl,
            p2x = rgrad.grad.x2,
            p2y = rgrad.grad.y2,
            r2 = rgrad.grad.r2*scl;
      let tp1 = matrixTransformPoint(obj.netTfm, {x:p1x, y:p1y});
      let tp2 = matrixTransformPoint(obj.netTfm, {x:p2x, y:p2y});
      if (obj.type === "IMG" && !this.yDown)    // IMG is flipped vertically, don't flip the gradient
      {
        const m = matrixScale(obj.netTfm, 1, -1);  // flip vertically
        tp1 = matrixTransformPoint(obj.netTfm, {x:p1x, y:-p1y});
        tp2 = matrixTransformPoint(obj.netTfm, {x:p2x, y:-p2y});
      }
      
      const grad = this.ctx.createRadialGradient(tp1.x, tp1.y, r1, tp2.x, tp2.y, r2);
      rgrad.colorStops.forEach((colStop)=>{
        grad.addColorStop(colStop.stop, colStop.color);
      });

      return grad;
    }

    resetClip()
    {
      // always called at end of render to ensure no stray clip masks
      while (this.clipCount > 0)
      {
        this.ctx.restore();   // restore raw pixel, default style saved at line 2818 
        this.clipCount--;
      }
    }

    genLinGradWC(lgrad)
    {
      const grad = this.ctx.createLinearGradient(lgrad.grad.x1, lgrad.grad.y1*this.isoYscl, 
                                                lgrad.grad.x2, lgrad.grad.y2*this.isoYscl);
      lgrad.colorStops.forEach((colStop)=>{
        grad.addColorStop(colStop.stop, colStop.color);
      });

      return grad;
    }

    genRadGradWC(rgrad)
    {
      const grad = this.ctx.createRadialGradient(rgrad.grad.x1, rgrad.grad.y1*this.isoYscl, rgrad.grad.r1, 
                                                rgrad.grad.x2, rgrad.grad.y2*this.isoYscl, rgrad.grad.r2);
      rgrad.colorStops.forEach((colStop)=>{
        grad.addColorStop(colStop.stop, colStop.color);
      });
      return grad;
    }

    drawPath(pathDef, options)
    {
      const pathObj = new Path(pathDef, options);

      this.render(pathObj);
    }

    drawShape(pathDef, options)
    {
      // outline the same as fill color
      const pathObj = new Shape(pathDef, options);

      this.render(pathObj);
    }

    drawText(str, options)
    {
      const txtObj = new Text(str, options);

      this.render(txtObj);
    }

    drawImg(imgRef, options)  // just load img then call render
    {
      const imgObj = new Img(imgRef, options);

      this.render(imgObj);
    }

    clearShape(pathDef, options)
    {
      // outline the same as fill color
      const pathObj = new Shape(pathDef, options);

      // set the clear flag for paintShape
      pathObj.clearFlag = true;
      this.render(pathObj);
    }

    createLayer()
    {
      const w = this.rawWidth,
            h = this.rawHeight,
            nLyrs = this.bkgCanvas.layers.length;  // bkg is layer 0 so at least 1

      // do not create layers on overlays or offscreen canvases - only an background canvases
      if (this.cgoType === "OVL" || this.cgoType === "OS")
      {
        // this is an overlay canvas - can't have overlays itself
        console.warn("createLayer: offscreen canvases and layers cannot create layers");
        return "";
      }

      const ovlId = this.cId+"_ovl_"+this.getUnique();
      const ovlHTML = "<canvas id='"+ovlId+"' style='position:absolute' width='"+w+"' height='"+h+"'></canvas>";
      const topCvs = this.bkgCanvas.layers[nLyrs-1].cElem;  // eqv to this.cnvs.layers since only bkgCanavs can get here
      topCvs.insertAdjacentHTML('afterend', ovlHTML);
      const newCvs = document.getElementById(ovlId);
      newCvs.style.backgroundColor = "transparent";
      newCvs.style.left = (this.bkgCanvas.offsetLeft+this.bkgCanvas.clientLeft)+'px';
      newCvs.style.top = (this.bkgCanvas.offsetTop+this.bkgCanvas.clientTop)+'px';
      // make it the same size as the background canvas
      newCvs.style.width = this.bkgCanvas.offsetWidth+'px';
      newCvs.style.height = this.bkgCanvas.offsetHeight+'px';
      const newL = new Layer(ovlId, newCvs);
      // save the ID in an array to facilitate removal
      this.bkgCanvas.layers.push(newL);

      return ovlId;    // return the new canvas id for call to new Cango(id)
    }

    deleteLayer(ovlyId)
    {
      for (let i=1; i<this.bkgCanvas.layers.length; i++)
      {
        if (this.bkgCanvas.layers[i].id === ovlyId)
        {
          const ovlNode = this.bkgCanvas.layers[i].cElem;
          if (ovlNode)
          {
            // in case the CangoHTMLtext extension is used
            if (ovlNode.alphaOvl && ovlNode.alphaOvl.parentNode)
            {
              ovlNode.alphaOvl.parentNode.removeChild(ovlNode.alphaOvl);
            }
            ovlNode.parentNode.removeChild(ovlNode);
          }
          // now delete layers array element
          this.bkgCanvas.layers.splice(i,1);       // delete the id
        }
      }
    }

    deleteAllLayers()
    {
      for (let i = this.bkgCanvas.layers.length-1; i>0; i--)   // don't delete layers[0] its the bkg canvas
      {
        const ovlNode = this.bkgCanvas.layers[i].cElem;
        if (ovlNode)
        {
          // in case the CangoHTMLtext extension is used
          if (ovlNode.alphaOvl && ovlNode.alphaOvl.parentNode)
          {
            ovlNode.alphaOvl.parentNode.removeChild(ovlNode.alphaOvl);
          }
          ovlNode.parentNode.removeChild(ovlNode);
        }
        // now delete layers array element
        this.bkgCanvas.layers.splice(i,1);
      }
    }

    // copy the basic graphics context values (for an overlay)
    dupCtx(src_graphCtx)
    {
      // copy all the graphics context parameters into the overlay ctx.
      this.vpW = src_graphCtx.vpW;              // gridbox (viewport) width in pixels
      this.vpH = src_graphCtx.vpH;              // gridbox height in pixels
      this.vpOrgX = src_graphCtx.vpOrgX;        // gridbox origin X in pixels
      this.vpOrgYsvg = src_graphCtx.vpOrgYsvg;  // needed when switching between RHC and SVG and back
      this.vpOrgYrhc = src_graphCtx.vpOrgYrhc;  //   "
      this.vpOrgY = src_graphCtx.vpOrgY;        // gridbox origin Y in pixels 
      this.vpOrgXWC = src_graphCtx.vpOrgXWC;    // gridbox origin X in World Coords
      this.vpOrgYWC = src_graphCtx.vpOrgYWC;    // gridbox origin Y in World Coords
      this.vpWWC = src_graphCtx.vpWWC;          // gridbox width in World Coords
      this.vpHWC = src_graphCtx.vpHWC;          // gridbox height in World Coords
      this.xscl = src_graphCtx.xscl;            // world x axis scale factor
      this.yscl = src_graphCtx.yscl;            // world y axis scale factor
      this.yDown = src_graphCtx.yDown;          // set by setWorldCoordsRHC or setWorldCoordsSVG to signal coord system
      this.isoYscl = src_graphCtx.isoYscl;      // drawing is done with iso coords (updated prior to render)
      this.xoffset = src_graphCtx.xoffset;      // world x origin offset from viewport left in pixels
      this.yoffset = src_graphCtx.yoffset;      // world y origin offset from viewport bottom in pixels
      this.savWCscl = structuredClone(src_graphCtx.savWCscl);
      this.savGB = structuredClone(src_graphCtx.savGB);
      this.strokeColDef = src_graphCtx.strokeColDef.slice(0); // copy value not reference
      this.lineWidthDef = src_graphCtx.lineWidthDef;          // pixels
      this.lineCapDef = src_graphCtx.lineCapDef.slice(0);
      this.lineJoinDef = src_graphCtx.lineJoinDef.slice(0);
      this.fillColDef = src_graphCtx.fillColDef.slice(0);
      this.fontSizeDef = src_graphCtx.fontSizeDef;
      this.fontWeightDef = src_graphCtx.fontWeightDef;
      this.fontFamilyDef = src_graphCtx.fontFamilyDef.slice(0);
    }
  };

}());
