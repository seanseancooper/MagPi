/*===================================================================
  Filename: CangoAxes-10v06.js
  Rev 10
  By: Dr A.R.Collins

  Requires Cango-26 or greater
  Description: Adds methods to Cango core to facilitate drawing graph 
  axes. It also adds the utility functions:
    sprintf, 
    toEngFixed, 
    toEngPrec, 
    toEngNotation, 
    toSciNotation

  Copyright 2024 A.R.Collins
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

  Date    Description                                            |By
  -------------------------------------------------------------------
  30Apr14 First beta                                              ARC
  11May14 Released as CangoAxes-1v00                              ARC
  28Mar17 Released as CangoAxes-2v00                              ARC
  10Jul17 Released as CangoAxes-3v00                              ARC
  20Jul17 Released as CangoAxes-4v00                              ARC
  29May19 Released as CangoAxes-5v00                              ARC
  12Aug19 Released as CangoAxes-6v00                              ARC
  24Aug19 bugfix: gridColor option not being honored              ARC
  09Nov19 Force hard transforms follow in insertion order
          Force drawHTMLtext options also follow insertion order  ARC
  11Nov19 Released as CangoAxes-7v00                              ARC
  12Jul20 Split off Text methods into CangoTextUtils              ARC
  12Jul20 Released as CangoAxes-8v00                              ARC
  14Jun21 Upgrade to uses Cango-22
          Released as CangoAxes-9v00                              ARC
  28Jun21 Simplify immediate execute wrapper                      ARC
  22Mar22 Add Xaxis and Yaxis objects
          Removed the option to reverse the X axis direction      ARC
  08Apr22 Rename setProperty to setStyleProperty                  ARC
  12Apr22 Released as CangoAxes-10v00                             ARC
  19Apr22 Update to use CangoTextUtiles-4v02
          bugfix: Axes xUnits and yUnits not passed due to typo   ARC
  18Apr23 Update to Cango-24, use 'rot' not 'degs' for angles     ARC
  27Apr23 bugfix: bad argument for toSciNotation                  ARC
  27Apr23 bugfix: bad argument for toSciNotation                  ARC
  27Feb25 bugfix: drawing in preRender is lost if clear==true     ARC
 ====================================================================*/

var Axes, BoxAxes, Xaxis, Yaxis, sprintf, toEngFixed, toEngPrec, toEngNotation, toSciNotation;

(function()
{
  "use strict";
  toEngFixed = function(val, decPlaces)      // rounds to X dec places and no stripping of 0s
  {
    const unit = "pnum kMGT";
    let man = 0,
        exp = 0,
        str = "";

    if ((decPlaces === undefined)||(decPlaces<0)||(decPlaces>10))
    {
      decPlaces = 2;
    }
    if (Math.abs(val)>1.0E-12)
    {
      exp = Math.floor(Math.log(Math.abs(val))/(3.0*Math.LN10));
      man = val/Math.pow(1000.0, exp);
      exp *= 3;
    }
    // now force round to decPlaces
    str = man.toFixed(decPlaces);
    // now add the symbol for the exponent
    return str+unit.charAt(exp/3+4);
  };

  toEngPrec = function(val, sigFigs, showPlus)   // rounds to X significant figures, maintains returned string length
  {
    const unit = "pnum kMGT";
    let man = 0, 
        delta,
        exp = 0,
        str = "";

    if ((sigFigs === undefined)||(sigFigs<3)||(sigFigs>10))
    {
      sigFigs = 3;
    }
    delta = 1+Math.pow(10, -sigFigs);
    if (Math.abs(val)>1.0E-12)
    {
      exp = Math.floor(Math.log(Math.abs(delta*val))/(3.0*Math.LN10));
      man = val/Math.pow(1000.0, exp);
      exp *= 3;
    }
    // now force round to sigFigs
    str = man.toPrecision(sigFigs);
    if (man >= 0)  // add a space for the "-" sign so string length is constant regardless of the number
    {
      str = (showPlus)? "+"+str:  " "+str;
    }
    if (str.indexOf(".") === -1)   // no decimal just 3 digits, add a leading space to maintain string length
    {
      return " "+str+unit.charAt(exp/3+4); // adding the symbol for the exponent
    }
    else
    {
      return str+unit.charAt(exp/3+4);
    }
  };

  toEngNotation = function(val, exponent)        // rounds to 2 dec places and strips trailing 0s
  {
    const unit = "pnum kMGT";
    const retObj = {};
    let man = 0,
        exp = 0,
        manStr = "",
        expStr = "";

    if (Math.abs(val)>1.0E-12)  // 0 is special man = 0, exp = ""
    {
      if (exponent !== undefined && (exponent % 3 == 0))  // a forced exponent must be multiple of 3
      {
        exp = exponent;
        man = val/Math.pow(10.0, exp);
      }
      else
      {
        exp = Math.floor(Math.log(Math.abs(val))/(3.0*Math.LN10));  // alow exponent over-ride
        man = val/Math.pow(1000.0, exp);
        exp *= 3;
      }
    }
    // now force round to decPlaces
    manStr = man.toFixed(2);
    // now strip trailing 0s
    while (manStr.charAt(manStr.length-1) === '0')
    {
      manStr = manStr.substring(0,manStr.length-1);
    }
    if (manStr.charAt(manStr.length-1) === '.')
    {
      manStr = manStr.substring(0,manStr.length-1);
    }
    // now get the symbol for the exponent
    if (exp)
    {
      expStr = unit.charAt(exp/3+4);
    }

    retObj.man = parseFloat(manStr);
    retObj.manStr = manStr;
    retObj.exp = exp;
    retObj.expStr = expStr;

    return retObj;
  };

  toSciNotation = function(val, exponent)        // rounds to 2 dec places and strips trailing 0s
  {
    const retObj = {};
    let man = 0,
        exp = 0,
        manStr,
        expStr;
  
    if (Math.abs(val)>1.0E-12)
    {
      if (exponent !== undefined)
      {
        exp = exponent;
      }
      else
      {
        exp = Math.floor(Math.log(Math.abs(val))/Math.LN10);  // alow exponent over-ride
      }
      man = val/Math.pow(10.0, exp);
    }
    // now force round to decPlaces
    manStr = man.toFixed(2);
    // now strip trailing 0s
    while (manStr.charAt(manStr.length-1) === '0')
    {
      manStr = manStr.substring(0, manStr.length-1);
    }
    if (manStr.charAt(manStr.length-1) === '.')  // don't end with deciamal point
    {
      manStr = manStr.substring(0, manStr.length-1);
    }
    expStr = exp.toString();
  
    retObj.man = parseFloat(manStr);
    retObj.manStr = manStr;
    retObj.exp = exp;
    retObj.expStr = expStr;

    return retObj;
  };

  function fRnd(a, decs=3)
  {
    const m = Math.pow(10, decs)
    return Math.round(a*m)/m;
  }
  
  function AxisTicsAuto(mn, mx, majorStep)
  {
    /* Calculate the tic mark spacing for graph plotting
     * Given the minimum and maximum values of the axis
     * returns the first tic value and the tic spacing.
     * The algorithm gives tic spacing of 1, 2, 5, 10, 20 etc
     * and a number of ticks from ~5 to ~11
     */
    let mj = majorStep || 0,   // may be number, "auto", or undefined
        pwr, 
        spanman, spanexp, 
        stepval, stepman, stepexp;

    this.tic1 = undefined;
    this.ticStep = undefined;   // avoid ticStep = 0 to avoid stepping by zero creating infinite loops
    this.lbl1 = undefined;
    this.lblStep = undefined;
    this.minTics = [];
    this.majTics = [];

    if (mn>=mx)
    {
      console.error("Axes Ticks: Max must be greater than Min");
      return;
    }

    pwr = Math.log(mx-mn)/Math.LN10;
    if (pwr<0.0)
    {
      spanexp = Math.floor(pwr) - 1;
    }
    else
    {
      spanexp = Math.floor(pwr);
    }
    spanman = (mx-mn)/Math.pow(10.0, spanexp);
    if(spanman>=5.5)
    {
      spanexp += 1;
      spanman /= 10.0;
    }
    stepman = 0.5;
    if(spanman<2.2)
    {
      stepman = 0.2;
    }
    if(spanman<1.1)
    {
      stepman = 0.1;
    }
    stepexp = 3*Math.floor(spanexp/3);
    if((spanexp < 0)&&(spanexp%3 !== 0))
    {
      stepexp -= 3;
    }
    stepval = stepman*Math.pow(10.0, (spanexp-stepexp));
    this.ticStep = stepval*Math.pow(10.0, stepexp);

    if(mn>=0.0)
    {
      this.tic1 = (Math.floor((mn/this.ticStep)-0.01)+1)*this.ticStep;   // avoid math noise
    }
    else
    {
      this.tic1 = -Math.floor((-mn/this.ticStep)+0.01)*this.ticStep;   // avoid math noise
    }

    // Calc the step size between major/labeled tics, it must be a multiple of ticStep
    if (mj === "auto")
    {
      this.lblStep = (stepman === 0.2)? this.ticStep*5: this.ticStep*2;
    }
		else if (mj)
		{
			this.lblStep = this.ticStep*Math.round(mj/this.ticStep);
		}
    const dx = 0.001*this.ticStep;
    if (this.lblStep)
    {
      this.lbl1 = this.lblStep*Math.ceil((mn-dx)/this.lblStep);
    }
    // build the tic arrays
    for (let i=0, x=this.tic1; x<mx+0.000000001; x+=this.ticStep)
    {
      let str = "";
      if (Math.abs(x-(this.lbl1+i*this.lblStep)) < 0.0001*this.ticStep )
      {
        if (Math.abs(x)<0.000000001) 
          x = 0;
        str = x.toPrecision(4);
        this.majTics.push(parseFloat(str));
        i++;
      }
      else
      {
        if (Math.abs(x)<0.000000001) 
          x = 0;
        str = x.toPrecision(4);
        this.minTics.push(parseFloat(str));
      }
    }
  }

  function AxisTicsManual(xmin, xmax,	xMn, xMj)
	{
    this.tic1 = undefined;
    this.ticStep = undefined;
    this.lbl1 = undefined;
    this.lblStep = undefined;
    this.minTics = [];
    this.majTics = [];

    // check for valid inputs, limit ticks to 1 < tickStep < 50
		if (xmin===undefined || xmax===undefined || xMn===undefined || xMn < (xmax-xmin)/50 || xMn >= (xmax-xmin))
    {
			return;
    }

		const dx = 0.01*xMn;
		this.tic1 = xMn*Math.ceil((xmin-dx)/xMn);
    this.ticStep = xMn;

		if (xMj !== undefined && xMj >= xMn && xMj < (xmax-xmin))
		{
			this.lblStep = this.ticStep*Math.round(xMj/xMn);
			this.lbl1 = this.lblStep*Math.ceil((xmin-dx)/this.lblStep);
    }

    for (let i=0, x=this.tic1; x<xmax+0.00000001; x+=this.ticStep)
    {
      if (Math.abs(x-(this.lbl1+i*this.lblStep)) < 0.0001*this.ticStep )
      {
        this.majTics.push(x);
        i++;
      }
      else
      {
        this.minTics.push(x);
      }
    }
	}

  Xaxis = class extends Group
  {
    constructor(xMin, xMax, opts={})
    {
      super();
      this.xMin = xMin;
      this.xMax = xMax;

      const setStyleProperty = (propertyName, value)=>
      {
        if ((typeof propertyName !== "string")||(value === undefined))  // null is OK, forces default
        {
          return;
        }
        switch (propertyName.toLowerCase())
        {
          case "xorigin":
            this.parms.xOrg = value;
            break;
          case "yorigin":
            this.parms.yOrg = value;
            break;
          case "xunits":
            if (typeof value === "string")
            {
              this.parms.xUnits = value;
            }
            break;
          case "xlabel":
          case "xaxislabel":
            if (typeof value === "string")
            {
              this.parms.xLabel = value;
            }
            break;
          case "xtickinterval":
          case "xminortickinterval":
            this.parms.xMinTic = value;
            break;
          case "xlabelinterval":
          case "xmajortickinterval":
            this.parms.xMajTic = value;
            break;
          case "xtickdir":
          case "xtickdirection":
            if (typeof value === "string")  // "up", "down", "cross"
            {
              this.parms.xtickDir = value;
            }
            break;
          case "strokecolor":
            this.parms.strokeColor = value;
            break;
          case "fillcolor":
            this.parms.fillColor = value;
            break;
          case "fontsize":
            this.parms.fontSize = Math.abs(value);
            break;
          case "fontweight":
            if (typeof value === "string" || ((typeof value === "number")&&(value>=100)&&(value<=900)))
            {
              this.parms.fontWeight = value;
            }
            break;
          case "fontfamily":
            if (typeof value === "string")
            {
              this.parms.fontFamily = value;
            }
            break
          default:
            return;
        }
      }
    
      this.parms = {
        xOrg: undefined,
        yOrg: undefined,
        xMinTic: "auto",
        xMajTic: "auto",
        xtickDir: "cross",
        xUnits: "",
        xLabel: "",
        strokeColor: "dimgray",
        fillColor: "black",
        fontSize: 11,
        fontWeight: "normal",
        fontFamily: "Arial, Verdana"
      };
      // check for all supported options
      for (let prop in opts)
      {
        // check that its opts's own property, not inherited from prototype
        if (opts.hasOwnProperty(prop))
        {
          setStyleProperty(prop, opts[prop]);
        }
      }
    }  // constructor

    preRender(gc)
    {
      function getTextWidth(txt, styleStr)
      {
        let wid = 0;

        gc.ctx.save();
        gc.ctx.font = styleStr;
        wid = gc.ctx.measureText(txt).width;  // width in pixels
        gc.ctx.restore();

        return wid;
      }

      let lorg = 1,
          side = 1,
          tickObj,
          majTickObj,
          ll, ur,
          xmin, xmax, ymin, ymax;
      // get WC of the gridbox to default to edge of plot area
      if (gc.yDown) // SVG vpOrg is upper left of gridbox
      {
        ll = gc.toWorldCoords(gc.vpOrgX, gc.vpOrgY+gc.vpH);
        ur = gc.toWorldCoords(gc.vpOrgX+gc.vpW, gc.vpOrgY);
        ymin = ur.y;
        ymax = ll.y;
      }
      else // RHC vpOrg is lower left of gridbox
      {
        ll = gc.toWorldCoords(gc.vpOrgX, gc.vpOrgY);
        ur = gc.toWorldCoords(gc.vpOrgX+gc.vpW, gc.vpOrgY-gc.vpH); // px -ve UP the screen so -vpH
        ymin = ll.y;
        ymax = ur.y;
      }
      xmin = (this.xMin === undefined)? ll.x : this.xMin;
      xmax = (this.xMax === undefined)? ur.x : this.xMax;
      const xOrg = (this.parms.xOrg === undefined)? xmin : this.parms.xOrg;
      const yOrg = (this.parms.yOrg === undefined)? ymin : this.parms.yOrg;
      // find the size of chars in the selected font
      const fntStyle = this.parms.fontWeight+" "+this.parms.fontSize+"px "+this.parms.fontFamily;
      const exWid = getTextWidth("X", fntStyle);
      const exHgt = exWid;
      // draw all ticks defined in pixels and drawn in world coords (convert px/cgo.xscl with iso=true)
      const ticLen = exWid/gc.xscl;   
      const majTicLen = 1.7*ticLen; 
      const crsTick = new Path(['M', 0, -ticLen/3, 'L', 0, ticLen/3], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const crsMajTick = new Path(['M', 0, -majTicLen/3, 'L', 0, majTicLen/3], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const posTick = new Path(['M', 0, 0, 'L', 0, ticLen/2], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const posMajTick = new Path(['M', 0, 0, 'L', 0, majTicLen/2], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const negTick = new Path(['M', 0, 0, 'L', 0, -ticLen/2], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const negMajTick = new Path(['M', 0, 0, 'L', 0, -majTicLen/2], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});

      let xTkLbOfs = 0.8*exHgt/gc.yscl,   // convert pixel lengths to world coords
          xAxLbOfs = 1.9*exHgt/gc.yscl,   
          xL = "",
          xU = "",
          xTics,
          lastxVal,
          lastxFmt;
      
      if ((this.parms.xMinTic === undefined)||(this.parms.xMinTic === null)||(this.parms.xMinTic === "auto"))  // xMinTic===0 means no x ticks
      {
        xTics = new AxisTicsAuto(xmin, xmax, this.parms.xMajTic);
      }
      else
      {
        xTics = new AxisTicsManual(xmin, xmax, this.parms.xMinTic, this.parms.xMajTic);
      }
      // draw axis
      const ax = new Path(['M', xmin, yOrg, 'L', xmax, yOrg], {
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor
      });
      this.addObj(ax);

      // X axis tick marks
      if (xTics.ticStep)
      {
        if (this.parms.xtickDir == "up")
        {
          tickObj = (gc.yDown)? negTick: posTick;
          majTickObj = (gc.yDown)? negMajTick: posMajTick;
        }
        else if (this.parms.xtickDir == "down")
        {
          tickObj = (gc.yDown)? posTick: negTick;
          majTickObj = (gc.yDown)? posMajTick: negMajTick;
        }
        else  // use cross ticks
        {
          tickObj = crsTick;
          majTickObj = crsMajTick;
          xTkLbOfs *= 1.3;    // allow for half tick being on same side as label
        }
        
        xTics.minTics.forEach( (x)=>{
          tickObj.translate(x, yOrg);
          gc.render(tickObj);   
        });
        xTics.majTics.forEach( (x)=>{
          majTickObj.translate(x, yOrg);
          gc.render(majTickObj);
        });
        }
      
      // label X axis major ticks (only if lblStep !-- 0)
      if (xTics.lblStep)
      {
        // calc x exponent of last tick and use for all label values
        lastxVal = xTics.minTics[xTics.minTics.length-1];
        lastxFmt = toEngNotation(lastxVal);
        // X axis, decide whether to label above or below X axis
        if (gc.yDown)  // SVG
        {
          if (yOrg < ymin + 0.55*(ymax - ymin))
          {   // x axis in top half of screen
            side = 1;
            lorg = 8;
          }
          else  // bottom half
          {
            side = -1;
            lorg = 2;
          }
        }
        else // RHC
        {
          if (yOrg < ymin + 0.55*(ymax - ymin))
          {   // x axis on bottom half of screen
            side = -1;
            lorg = 2;
          }
          else
          {
            side = 1;
            lorg = 8;
          }
        }
        if ((this.parms.xtickDir == "down" && fRnd(yOrg) == fRnd(ymin))
        || (this.parms.xtickDir == "up" && fRnd(yOrg) == fRnd(ymax)))
        { // ticks will be between axis and label, make gap bigger
          xTkLbOfs += 0.6*ticLen*gc.xscl/gc.yscl;
        }
        xTics.majTics.forEach((x)=>{
          // skip label at the origin if it would hit Y axis
          if (fRnd(x) == fRnd(xOrg) && yOrg > ymin && yOrg < ymax)
          {
            return;
          }
          const xt = new Text(toEngNotation(x, lastxFmt.exp).manStr, {
            x: x,
            y: yOrg - side*xTkLbOfs,
            lorg: lorg,
            fillColor: this.parms.fillColor,
            fontSize: this.parms.fontSize,
            fontWeight: this.parms.fontWeight,
            fontFamily: this.parms.fontFamily });
          this.addObj(xt);
        });
      }

      // X axis label and units
      let x;
      if (gc.yDown)
      {
        if (yOrg < ymin+0.55*(ymax-ymin))  // bottom of graph
        {
          side = 1;
          if ((xOrg != xmin && xOrg != xmax) && yOrg != ymax)
          { // label xmax
            lorg = 9;
            x = xmax;
          }
          else
          {  // label center
            lorg = 8;
            x = (xmin+xmax)/2;
          }
        }
        else                            // top of graph
        {
          side = -1;
          if ((xOrg != xmin && xOrg != xmax) && yOrg != ymin)
          { // label xmax
            lorg = 3;
            x = xmax;
          }
          else
          {  // label center
            lorg = 2;
            x = (xmin+xmax)/2;
          }
        }
      }
      else    // RHC
      {
        if (yOrg < ymin+0.55*(ymax-ymin))   // bottom of graph
        {
          side = -1;
          if ((xOrg != xmin && xOrg != xmax)&& (Math.abs(yOrg-ymin) > Math.abs(0.01*ymin)))
          { // label xmax    
            lorg = 3;
            x = xmax;
          }
          else                          
          {  // label center
            lorg = 2;
            x = (xmin+xmax)/2;
          }
        }
        else                            // top of graph
        {
          side = 1;
          if ((xOrg != xmin && xOrg != xmax) && (Math.abs(yOrg-ymax) > Math.abs(0.01*ymax)))
          { // label xmax
            lorg = 9;
            x = xmax;
          }
          else
          {  // label center
            lorg = 8;
            x = (xmin+xmax)/2;
          }
        }
      }

      xL = xL+this.parms.xLabel;
      if (!xTics.lblStep)  // we may have an axis label and no tick labels or units
      {
        if (xL.length>0)
        {
          const xlb = new Text(xL, {
            x: x, 
            y: yOrg - side*xAxLbOfs,
            lorg: lorg,
            fillColor: this.parms.fillColor,
            fontSize: this.parms.fontSize*1.1,
            fontWeight: this.parms.fontWeight,
            fontFamily: this.parms.fontFamily });
          this.addObj(xlb);
        }
        return;
      }
      xAxLbOfs += 1.2*xTkLbOfs;
      if (this.parms.xUnits.length) // add units if we have any
      {
        xL = xL+" ("+lastxFmt.expStr+this.parms.xUnits+")";
        const xlb = new Text(xL, {
          x: x, 
          y: yOrg - side*xAxLbOfs,
          lorg: lorg,
          fillColor: this.parms.fillColor,
          fontSize: this.parms.fontSize*1.1,
          fontWeight: this.parms.fontWeight,
          fontFamily: this.parms.fontFamily });
        this.addObj(xlb);
      }   
      else   // we have no units, use scientific notation
      { 
        xU = toSciNotation(10, lastxFmt.exp);  // object 
        if (xU.expStr == "0") // dont draw sciNotation units if 10^0 
        {
          if (xL.length>0) // just draw the xlabel (if any)
          {
            const xul = new Text(xL, {
              x: x, 
              y: yOrg - side*xAxLbOfs,
              lorg: lorg,
              fillColor: this.parms.fillColor,
              fontSize: this.parms.fontSize*1.1,
              fontWeight: this.parms.fontWeight,
              fontFamily: this.parms.fontFamily });
            this.addObj(xul);
          }
        }
        else  // we have sciNotation units to draw
        {
          const xul = new SciNotationText(lastxVal, {
            x: x, 
            y: yOrg - side*xAxLbOfs,
            preText: xL+"  \uff08",     // prepend the axis label + "("
            postText: "\uff09",         // append ")"
            lorg: lorg,
            fillColor: this.parms.fillColor,
            fontSize: this.parms.fontSize*1.1,
            fontWeight: this.parms.fontWeight,
            fontFamily: this.parms.fontFamily });
          this.addObj(xul);
        }
      }
    }
  };  // Xaxis

  Yaxis = class extends Group
  {
    constructor(yMin, yMax, opts={})
    {
      super();
      this.yMin = yMin;
      this.yMax = yMax;

      const setStyleProperty = (propertyName, value)=>
      {
        if ((typeof propertyName !== "string")||(value === undefined))  // null is OK, forces default
        {
          return;
        }
        switch (propertyName.toLowerCase())
        {
          case "xorigin":
            this.parms.xOrg = value;
            break;
          case "yorigin":
            this.parms.yOrg = value;
            break;
          case "yunits":
            if (typeof value === "string")
            {
              this.parms.yUnits = value;
            }
            break;
          case "ylabel":
          case "yaxislabel":
            if (typeof value === "string")
            {
              this.parms.yLabel = value;
            }
            break;
          case "ytickinterval":
          case "yminortickinterval":
            this.parms.yMinTic = value;
            break;
          case "ylabelinterval":               
          case "ymajortickinterval":
            this.parms.yMajTic = value;
            break;
          case "ytickdir":
          case "ytickdirection":
            if (typeof value === "string")  // "left", "right", "cross"
            {
              this.parms.ytickDir = value;
            }
            break;
          case "strokecolor":
            this.parms.strokeColor = value;
            break;
          case "fillcolor":
            this.parms.fillColor = value;
            break;
          case "fontsize":
            this.parms.fontSize = Math.abs(value);
            break;
          case "fontweight":
            if (typeof value === "string" || ((typeof value === "number")&&(value>=100)&&(value<=900)))
            {
              this.parms.fontWeight = value;
            }
            break;
          case "fontfamily":
            if (typeof value === "string")
            {
              this.parms.fontFamily = value;
            }
            break;
          default:
          return;
        }
      }
    
      this.parms = {
        xOrg: undefined,
        yOrg: undefined,
        yMinTic: "auto",
        yMajTic: "auto",
        ytickDir: "cross",
        yUnits: "",
        yLabel: "",
        strokeColor: "dimgray",
        fillColor: "black",
        fontSize: 11,
        fontWeight: "normal",
        fontFamily: "Arial, Verdana"
      };
      // check for all supported options
      for (let prop in opts)
      {
        // check that its opts's own property, not inherited from prototype
        if (opts.hasOwnProperty(prop))
        {
          setStyleProperty(prop, opts[prop]);
        }
      }
    }  // constructor

    preRender(gc)
    {
      function getTextWidth(txt, styleStr)
      {
        let wid = 0;

        gc.ctx.save();
        gc.ctx.font = styleStr;
        wid = gc.ctx.measureText(txt).width;  // width in pixels
        gc.ctx.restore();

        return wid;
      }

      let lorg = 1,
          side = 1,
          tickObj,
          majTickObj,
          ll, ur,
          xmin, xmax, ymin, ymax;
      // get WC of the gridbox to default to edge of plot area
      if (gc.yDown) // SVG vpOrg is upper left of gridbox
      {
        ll = gc.toWorldCoords(gc.vpOrgX, gc.vpOrgY+gc.vpH);
        ur = gc.toWorldCoords(gc.vpOrgX+gc.vpW, gc.vpOrgY);
        ymin = (this.yMin === undefined)? ur.y : this.yMin;
        ymax = (this.yMax === undefined)? ll.y : this.yMax;
      }
      else // RHC vpOrg is lower left of gridbox
      {
        ll = gc.toWorldCoords(gc.vpOrgX, gc.vpOrgY);
        ur = gc.toWorldCoords(gc.vpOrgX+gc.vpW, gc.vpOrgY-gc.vpH); // px -ve UP the screen so -vpH
        ymin = (this.yMin === undefined)? ll.y : this.yMin;
        ymax = (this.yMax === undefined)? ur.y : this.yMax;
      }
      xmin = (this.xMin === undefined)? ll.x : this.xMin;
      xmax = (this.xMax === undefined)? ur.x : this.xMax;
      const xOrg = (this.parms.xOrg === undefined)? xmin : this.parms.xOrg;
      const yOrg = (this.parms.yOrg === undefined)? ymin : this.parms.yOrg;
      // find the size of chars in the selected font
      const fntStyle = this.parms.fontWeight+" "+this.parms.fontSize+"px "+this.parms.fontFamily;
      const exWid = getTextWidth("X", fntStyle);
      // draw all ticks defined in pixels and drawn in world coords (convert px/cgo.xscl with iso=true)
      const ticLen = exWid/gc.xscl;   
      const majTicLen = 1.7*ticLen; 
      const midTick = new Path(['M', -ticLen/3, 0, 'L', ticLen/3, 0], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const midMajTick = new Path(['M', -majTicLen/3.5, 0, 'L', majTicLen/3.5, 0], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const lftTick = new Path(['M', 0, 0, 'L', -ticLen/2, 0], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const lftMajTick = new Path(['M', 0, 0, 'L', -majTicLen/2, 0], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const rgtTick = new Path(['M', 0, 0, 'L', ticLen/2, 0], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});
      const rgtMajTick = new Path(['M', 0, 0, 'L', majTicLen/2, 0], {
        iso:true,
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor});

      let yTkLbOfs = 0.8*exWid/gc.xscl,
          yAxLbOfs = 1.1*exWid/gc.xscl,  // add label length etc later
          yL = "", 
          yU = "",
          yTics,
          lastyVal,
          lastyFmt;   

      if ((this.parms.yMinTic === undefined)||(this.parms.yMinTic === null)||(this.parms.yMinTic === "auto"))  // yMinTic===0 means no y ticks
      {
        yTics = new AxisTicsAuto(ymin, ymax, this.parms.yMajTic);
      }
      else
      {
        yTics = new AxisTicsManual(ymin, ymax, this.parms.yMinTic, this.parms.yMajTic);
      }
      // draw axis
      const ax = new Path(['M', xOrg, ymin, 'L', xOrg, ymax], {
        lineWidth:1.5,
        lineCap:"round",
        strokeColor:this.parms.strokeColor
      });
      this.addObj(ax);
      // Y axis tick marks
      if (yTics.ticStep)
      {
        if (this.parms.ytickDir == "cross")
        {
          tickObj = midTick;
          majTickObj = midMajTick;
          yTkLbOfs *= 1.3;    // allow for half tick being on same side as label
        }
        else
        {
          tickObj = (this.parms.ytickDir == "right")? rgtTick: lftTick;
          majTickObj = (this.parms.ytickDir == "right")? rgtMajTick: lftMajTick;
        }

        yTics.minTics.forEach( (y)=>{
          tickObj.translate(xOrg, y);
          gc.render(tickObj);
        })
        yTics.majTics.forEach( (y)=>{
          majTickObj.translate(xOrg, y);
          gc.render(majTickObj);
        })
      }

      // Y axis major tick labels (only if lblStep !-- 0)
      if (yTics.lblStep)
      {
        // calc x exponent of last tick and use for all label values
        lastyVal = yTics.minTics[yTics.minTics.length-1];
        lastyFmt = toEngNotation(lastyVal);
        // Y axis, decide whether to label to right or left of Y axis
        if (xOrg < xmin+0.5*(xmax-xmin))
        {  // y axis on left half of screen
          side = -1;
          lorg = 6;
        }
        else
        {
          side = +1;
          lorg = 4;
        }

        if ((this.parms.ytickDir == "left" && fRnd(xOrg) == fRnd(xmin))
            || (this.parms.ytickDir == "right" && xOrg > xmax*0.999))
        { // ticks will be between axis and label, make gap bigger
          yTkLbOfs += ticLen/2;
        } 

        yTics.majTics.forEach( (y)=>{
          // skip label at the origin if it would hit X axis
          if (fRnd(y) == fRnd(yOrg) && xOrg > xmin && xOrg < xmax)
          {
            return;
          }
          const mt = new Text(toEngNotation(y, lastyFmt.exp).manStr, {
            x: xOrg + side*yTkLbOfs,
            y: y,
            lorg: lorg,
            fillColor: this.parms.fillColor,
            fontSize: this.parms.fontSize,
            fontWeight: this.parms.fontWeight,
            fontFamily: this.parms.fontFamily});
          this.addObj(mt);
        }); 
      }

      // Y axis label and units
      let y;
      // Y axis, decide whether to label to right or left of Y axis
      if (xOrg < xmin+0.5*(xmax-xmin))
      {
        // y axis on left half of screen
        side = -1;
        if (yOrg != ymin && yOrg != ymax)
        { // label ymax
          lorg = (gc.yDown)? 7: 9;
          y = ymax;
        }
        else
        { // label center
          lorg = 8;
          y = (ymin+ymax)/2;
        }
      }
      else
      {
        // y axis on right half of screen
        side = 1;
        if (yOrg != ymin && yOrg != ymax)
        { 
          lorg = (gc.yDown)? 1: 3;
          y = ymax;
        }
        else
        { // label center
          lorg = 2;
          y = (ymin+ymax)/2;
        }
      }
      yL = yL+this.parms.yLabel;
      if (!yTics.lblStep)  // we may have an axis label and no tick labels or units
      {
        if (yL.length>0)
        {
          const ylb = new Text(yL, {
            rot: (gc.yDown)? -90: 90,
            x: xOrg + side*yAxLbOfs, 
            y: y,
            lorg: lorg,
            fillColor: this.parms.fillColor,
            fontSize: this.parms.fontSize*1.1,
            fontWeight: this.parms.fontWeight,
            fontFamily: this.parms.fontFamily });
          this.addObj(ylb);
        }
        return;
      }
      // we have ticks, find width of longest tick label to position axis label
      let maxWid = yTics.majTics.reduce( (acc, curr)=>{
        return Math.max(acc, getTextWidth(toEngNotation(curr, lastyFmt.exp).manStr, fntStyle));
      }, 0);
      yAxLbOfs += maxWid/gc.xscl;

      if (this.parms.ytickDir == "left" && (fRnd(xOrg) == fRnd(xmin)))
      { // ticks will be between axis and label, make gap bigger
        yAxLbOfs += yTkLbOfs;
      } 
      else if (this.parms.ytickDir == "right" && (fRnd(xOrg) == fRnd(xmax)))
      { // ticks will be between axis and label, make gap bigger
        yAxLbOfs -= yTkLbOfs;
      } 
      if (this.parms.yUnits.length>0) // add units if we have any
      { 
        yL = yL+" ("+lastyFmt.expStr+this.parms.yUnits+")";
        const ylb = new Text(yL, {
          rot: (gc.yDown)? -90: 90,
          x: xOrg + side*yAxLbOfs, 
          y: y,
          lorg: lorg,
          fillColor: this.parms.fillColor,
          fontSize: this.parms.fontSize*1.1,
          fontWeight: this.parms.fontWeight,
          fontFamily: this.parms.fontFamily });
        this.addObj(ylb);
      }
      else   // we have no units, use scientific notation
      { // use sciNotation
        yU = toSciNotation(10, lastyFmt.exp);  // object 
        if (yU.expStr == "0") // dont draw if 10^0 
        {
          if (yL.length>0) // just draw the xlabel (if any)
          {
            const yul = new Text(yL, {
              rot: (gc.yDown)? -90: 90,
              x: xOrg + side*yAxLbOfs, 
              y: y,
              lorg:lorg,
              fillColor: this.parms.fillColor,
              fontSize: this.parms.fontSize*1.1,
              fontWeight: this.parms.fontWeight,
              fontFamily: this.parms.fontFamily });
            this.addObj(yul);
          }
        }
        else // we have sciNotation units to draw (not == 10^0)
        {
          const yul = new SciNotationText(lastyVal, {
            rot: (gc.yDown)? -90: 90,
            x: xOrg + side*yAxLbOfs, 
            y: y,
            preText: yL+"  \uff08",       // prepend the axis label + "("
            postText: "\uff09",           // append ")"
            lorg:lorg,
            fillColor: this.parms.fillColor,
            fontSize: this.parms.fontSize*1.1,
            fontWeight: this.parms.fontWeight,
            fontFamily: this.parms.fontFamily });
          this.addObj(yul);
        }
      }
    }
  };  // Yaxis

  Axes = class extends Group
  {
    constructor(xMin, xMax, yMin, yMax, opts={})
    {
      super();

      const setStyleProperty = (propertyName, value)=>
      {
        if ((typeof propertyName !== "string")||(value === undefined))  // null is OK, forces default
        {
          return;
        }
        switch (propertyName.toLowerCase())
        {
          case "xorigin":
            this.parms.xOrg = value;
            break;
          case "yorigin":
            this.parms.yOrg = value;
            break;
          case "xunits":
            if (typeof value === "string")
            {
              this.parms.xUnits = value;
            }
            break;
          case "yunits":
            if (typeof value === "string")
            {
              this.parms.yUnits = value;
            }
            break;
          case "xlabel":
          case "xaxislabel":
            if (typeof value === "string")
            {
              this.parms.xLabel = value;
            }
            break;
          case "ylabel":
          case "yaxislabel":
            if (typeof value === "string")
            {
              this.parms.yLabel = value;
            }
            break;
          case "xtickinterval":
          case "xminortickinterval":
            this.parms.xMinTic = value;
            break;
          case "ytickinterval":
          case "yminortickinterval":
            this.parms.yMinTic = value;
            break;
          case "xlabelinterval":
          case "xmajortickinterval":
            this.parms.xMajTic = value;
            break;
          case "ylabelinterval":               
          case "ymajortickinterval":
            this.parms.yMajTic = value;
            break;
          case "xtickdir":
          case "xtickdirection":
            if (typeof value === "string")  // up, down or cross
            {
              this.parms.xtickDir = value;
            }
            break;
          case "ytickdir":
          case "ytickdirection":
            if (typeof value === "string")  // left, right or cross
            {
              this.parms.ytickDir = value;
            }
            break;
          case "strokecolor":
            this.parms.strokeColor = value;
            break;
          case "fillcolor":
            this.parms.fillColor = value;
            break;
          case "fontsize":
            this.parms.fontSize = Math.abs(value);
            break;
          case "fontweight":
            if (typeof value === "string" || ((typeof value === "number")&&(value>=100)&&(value<=900)))
            {
              this.parms.fontWeight = value;
            }
            break;
          case "fontfamily":
            if (typeof value === "string")
            {
              this.parms.fontFamily = value;
            }
            break;
          default:
            return;
        }
      }
    
      this.parms = {
        xOrg: undefined,
        yOrg: undefined,
        xMinTic: "auto",
        yMinTic: "auto",
        xMajTic: "auto",
        yMajTic: "auto",
        xtickDir: "up",
        ytickDir: "right",
        xUnits: "",
        yUnits: "",
        xLabel: "",
        yLabel: "",
        strokeColor: "dimgray",
        fillColor: "black",
        fontSize: 11,
        fontWeight: "normal",
        fontFamily: "Arial, Verdana"
      };
      // check for all supported options
      for (let prop in opts)
      {
        // check that its opts's own property, not inherited from prototype
        if (opts.hasOwnProperty(prop))
        {
          setStyleProperty(prop, opts[prop]);
        }
      }
      const xaxis = new Xaxis(xMin, xMax, {
        xorigin: this.parms.xOrg,
        yorigin: this.parms.yOrg,
        xunits: this.parms.xUnits,
        xaxislabel: this.parms.xLabel,
        xtickinterval: this.parms.xMinTic,
        xmajortickinterval: this.parms.xMajTic,
        xtickdirection: this.parms.xtickDir,
        strokecolor: this.parms.strokeColor,
        fillcolor: this.parms.fillColor,
        fontsize: this.parms.fontSize,
        fontweight: this.parms.fontWeight,
        fontfamily: this.parms.fontFamily
      });

      const yaxis = new Yaxis(yMin, yMax, {
        xorigin: this.parms.xOrg,
        yorigin: this.parms.yOrg,
        yunits: this.parms.yUnits,
        yaxislabel: this.parms.yLabel,
        ytickinterval: this.parms.yMinTic,
        ymajortickinterval: this.parms.yMajTic,
        ytickdirection: this.parms.ytickDir,
        strokecolor: this.parms.strokeColor,
        fillcolor: this.parms.fillColor,
        fontsize: this.parms.fontSize,
        fontweight: this.parms.fontWeight,
        fontfamily: this.parms.fontFamily
      });

      super.addObj(xaxis, yaxis);     
    }  // constructor
  };

  BoxAxes = class extends Group
  {
    constructor(xMin, xMax, yMin, yMax, opts={})
    {
      super();
      this.xMin = xMin;
      this.xMax = xMax;
      this.yMin = yMin;
      this.yMax = yMax;

      const setStyleProperty = (propertyName, value)=>
      {
        if ((typeof propertyName !== "string")||(value === undefined))  // null is OK, forces default
        {
          return;
        }
        switch (propertyName.toLowerCase())
        {
          case "xunits":
            if (typeof value === "string")
            {
              this.parms.xUnits = value;
            }
            break;
          case "yunits":
            if (typeof value === "string")
            {
              this.parms.yUnits = value;
            }
            break;
          case "title":
            if (typeof value === "string")
            {
              this.parms.title = value;
            }
            break;
          case "xtickinterval":
            this.parms.xMinTic = value;
            break;
          case "ytickinterval":
            this.parms.yMinTic = value;
            break;
          case "strokecolor":
            this.parms.strokeColor = value;
            break;
          case "fillcolor":
            this.parms.fillColor = value;
            break;
          case "gridcolor":
            this.parms.gridColor = value;
            break;
          case "fontsize":
            this.parms.fontSize = Math.abs(value);
            break;
          case "fontweight":
            if (typeof value === "string"||(typeof value === "number" && value>=100 && value<=900))
            {
              this.parms.fontWeight = value;
            }
            break;
          case "fontfamily":
            if (typeof value === "string")
            {
              this.parms.fontFamily = value;
            }
            break;
          default:
            return;
        }
      }
    
      this.parms = { xMinTic: "auto",
        yMinTic: "auto",
        xUnits: "",
        yUnits: "",
        title: "",
        strokeColor: '#ffffff',
        fillColor: '#cccccc',
        gridColor: 'rgba(255,255,255,0.2)',
        fontSize: 11,
        fontWeight: null,
        fontFamily: "Arial, Verdana"
      };
      // check for all supported options
      for (let prop in opts)
      {
        // check that this is opts's own property, not inherited from prototype
        if (opts.hasOwnProperty(prop))
        {
          setStyleProperty(prop, opts[prop]);
        }
      }

    }  // constructor

    preRender(gc)
    {
      const ticLen = 4/gc.xscl,                           // 4 pixels
            tickRot = (gc.yDown)? -90: 90,
            xTkLbOfs = (gc.yDown)? 8/gc.yscl: -8/gc.yscl,  // pixels
            yTkLbOfs = 8/gc.xscl;                          // pixels
      let lbl, 
          lbl2 = "/div",
          xTics, 
          yTics;
    
      const tickCmds = new Path(['M', 0, 0, 'L', -ticLen, 0], {"strokeColor":this.parms.strokeColor, 'iso':true});

      if ((!this.parms.xMinTic)||(this.parms.xMinTic === "auto"))
      {
        xTics = new AxisTicsAuto(this.xMin, this.xMax);
      }
      else
      {
        xTics = new AxisTicsManual(this.xMin, this.xMax, this.parms.xMinTic);
      }
      if ((!this.parms.yMinTic)||(this.parms.yMinTic === "auto"))
      {
        yTics = new AxisTicsAuto(this.yMin, this.yMax);
      }
      else
      {
        yTics = new AxisTicsManual(this.yMin, this.yMax, this.parms.yMinTic);
      }
      // Draw box axes
      const data = ['M', this.xMin, this.yMin, 'L', this.xMin, this.yMax, this.xMax, this.yMax, this.xMax, this.yMin, 'z'];
      const pth = new Path(data, {strokeColor:this.parms.strokeColor});
      this.addObj(pth);

      xTics.minTics.forEach( (x)=>{
        const tpth = tickCmds.dup();
        tpth.rotate(tickRot);
        tpth.translate(x, this.yMin);
        this.addObj(tpth);  // ready to draw the tick mark
        if ((fRnd(x) !== fRnd(this.xMin)) && (fRnd(x) !== fRnd(this.xMax)))        // no dots on the box
        {
          const xt = new Path(['M', x, this.yMin, 'L', x, this.yMax], {strokeColor:this.parms.gridColor});
          this.addObj(xt);
        }
      });
      yTics.minTics.forEach( (y)=>{
        const tpth = tickCmds.dup();
        tpth.translate(this.xMin, y);
        this.addObj(tpth);      // ready to draw the tick mark
        if ((fRnd(y) !== fRnd(this.yMin)) && (fRnd(y) !== fRnd(this.yMax)))
        {
          const yt = new Path(['M', this.xMin, y, 'L', this.xMax, y], {strokeColor:this.parms.gridColor});
          this.addObj(yt);
        }
      });
      
      // Now labels, X axis, label only first and last tic below X axis
      // get the exponent of the step size, use this for all label
      const xstep = toEngNotation(xTics.ticStep);  // tick step as engNotation obj
        const tk = new Text(toEngNotation(xTics.tic1, xstep.exp).manStr, {
        x: xTics.tic1,
        y: this.yMin - xTkLbOfs,
        fillColor:this.parms.fillColor,
        lorg: (gc.yDown)? 7: 1,
        fontSize: this.parms.fontSize,
        fontWeight: this.parms.fontWeight,
        fontFamily: this.parms.fontFamily });
      this.addObj(tk);
      // find the last tick
      const lastxVal = xTics.minTics[xTics.minTics.length-1];
      const xv = new Text(toEngNotation(lastxVal, xstep.exp).manStr, {
          x: lastxVal,
          y: this.yMin - xTkLbOfs,
          fillColor: this.parms.fillColor,
          lorg: (gc.yDown)? 9: 3,
          fontSize: this.parms.fontSize,
          fontWeight: this.parms.fontWeight,
          fontFamily: this.parms.fontFamily });
      this.addObj(xv);
      // x axis label  
      lbl = xstep.manStr+" "+xstep.expStr+this.parms.xUnits+"/div";
      const lb = new Text(lbl, {
        x: this.xMin+(this.xMax-this.xMin)/2,
        y: this.yMin - xTkLbOfs,
        fillColor: this.parms.fillColor,
        lorg: (gc.yDown)? 8: 2,
        fontSize: this.parms.fontSize,
        fontWeight: this.parms.fontWeight,
        fontFamily: this.parms.fontFamily });
      this.addObj(lb);
      // Y axis, label bottom and top tics to left of Y axis
      // get the exponent of the step size, use this for all label
      const ystep = toEngNotation(yTics.ticStep);
      const ys = new Text(toEngNotation(yTics.tic1, ystep.exp).manStr, {
        x: this.xMin - yTkLbOfs,
        y: yTics.tic1,
        fillColor: this.parms.fillColor,
        lorg: 6,
        fontSize: this.parms.fontSize,
        fontWeight: this.parms.fontWeight,
        fontFamily: this.parms.fontFamily });
      this.addObj(ys);
      // find the last tick
      const lastyVal = yTics.minTics[yTics.minTics.length-1];
      const ly = new Text(toEngNotation(lastyVal, ystep.exp).manStr, {
        x: this.xMin - yTkLbOfs,
        y: lastyVal,
        fillColor: this.parms.fillColor,
        lorg: 6,
        fontSize: this.parms.fontSize,
        fontWeight: this.parms.fontWeight,
        fontFamily: this.parms.fontFamily });
      this.addObj(ly);
      // y axis label
      lbl = ystep.manStr+" "+ystep.expStr+this.parms.yUnits;
      if (!gc.yDown)
      {
        lbl2 = lbl.slice(0);       // copy lbl
        lbl = "/div";              // swap them
      }
      const ymid = this.yMin+(this.yMax-this.yMin)/2;
      const ym = new Text(lbl, {
        x: this.xMin - yTkLbOfs,
        y: ymid - xTkLbOfs,
        fillColor: this.parms.fillColor,
        lorg: 6,
        fontSize: this.parms.fontSize,
        fontWeight: this.parms.fontWeight,
        fontFamily: this.parms.fontFamily });
      this.addObj(ym);
      const lb2 = new Text(lbl2, {
        x: this.xMin - yTkLbOfs,
        y: ymid + xTkLbOfs,
        fillColor: this.parms.fillColor,
        lorg: 6,
        fontSize: this.parms.fontSize,
        fontWeight: this.parms.fontWeight,
        fontFamily: this.parms.fontFamily });
      this.addObj(lb2);
      // title
      if (typeof this.parms.title === "string")
      {
        const ttl = new Text(this.parms.title, {
          x: this.xMin,
          y: this.yMax + xTkLbOfs,
          fillColor: this.parms.fillColor,
          lorg: (gc.yDown)? 1: 7,
          fontSize: this.parms.fontSize,
          fontWeight: this.parms.fontWeight,
          fontFamily: this.parms.fontFamily });
        this.addObj(ttl);
      }
    }
	};

 /* ==========================================================================
  // http://kevin.vanzonneveld.net
  // +   original by: Ash Searle (http://hexmen.com/blog/)
  // + namespaced by: Michael White (http://getsprink.com)
  // +    tweaked by: Jack
  // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
  // +      input by: Paulo Freitas
  // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
  // +      input by: Brett Zamir (http://brett-zamir.me)
  // +   improved by: Kevin van Zonneveld (http://kevin.vanzonneveld.net)
  // +   improved by: Dj
  // +   improved by: Allidylls
  // *     example 1: sprintf("%01.2f", 123.1);
  // *     returns 1: 123.10
  // *     example 2: sprintf("[%10s]", 'monkey');
  // *     returns 2: '[    monkey]'
  // *     example 3: sprintf("[%'#10s]", 'monkey');
  // *     returns 3: '[####monkey]'
  // *     example 4: sprintf("%d", 123456789012345);
  // *     returns 4: '123456789012345'
 *==========================================================================*/
  sprintf = function()
  {
    var regex = /%%|%(\d+\$)?([\-\+\'#0 ]*)(\*\d+\$|\*|\d+)?(\.(\*\d+\$|\*|\d+))?([scboxXuideEfFgG])/g,
        a = arguments,
        i = 0,
        format = a[i++];

    function pad(str, len, chr, leftJustify)
    {
      var padding;

      if (!chr)
      {
        chr = ' ';
      }
      padding = (str.length >= len) ? '' : new Array(1 + len - str.length).join(chr);
      return leftJustify ? str + padding : padding + str;
    }

    // justify()
    function justify(value, prefix, leftJustify, minWidth, zeroPad, customPadChar)
    {
      var diff = minWidth - value.length;
      if (diff > 0)
      {
        if (leftJustify || !zeroPad)
        {
          value = pad(value, minWidth, customPadChar, leftJustify);
        }
        else
        {
          value = value.slice(0, prefix.length) + pad('', diff, '0', true) + value.slice(prefix.length);
        }
      }
      return value;
    }

    // formatBaseX()
    function formatBaseX(value, base, prefix, leftJustify, minWidth, precision, zeroPad)
    {
      // Note: casts negative numbers to positive ones
      var number = value >> 0;
      prefix = prefix && number && ({'2': '0b','8': '0', '16': '0x'}[base] || '');
      value = prefix + pad(number.toString(base), precision || 0, '0', false);
      return justify(value, prefix, leftJustify, minWidth, zeroPad);
    }

    // formatString()
    function formatString(value, leftJustify, minWidth, precision, zeroPad, customPadChar)
    {
      if (precision !== null)
      {
        value = value.slice(0, precision);
      }
      return justify(value, '', leftJustify, minWidth, zeroPad, customPadChar);
    }

    // doFormat()
    function doFormat(substring, valueIndex, flags, minWidth, _, precision, type)
    {
      var number,
          prefix,
          method,
          textTransform,
          value,
          leftJustify = false,
          positivePrefix = '',
          zeroPad = false,
          prefixBaseX = false,
          customPadChar = ' ',
          flagsl = flags.length,
          j;

      if (substring === '%%')
      {
        return '%';
      }

      for (j = 0; flags && j < flagsl; j++)
      {
        switch (flags.charAt(j))
        {
          case ' ':
            positivePrefix = ' ';
            break;
          case '+':
            positivePrefix = '+';
            break;
          case '-':
            leftJustify = true;
            break;
          case "'":
            customPadChar = flags.charAt(j + 1);
            break;
          case '0':
            zeroPad = true;
            break;
          case '#':
            prefixBaseX = true;
            break;
        }
      }

      // parameters may be null, undefined, empty-string or real valued
      // we want to ignore null, undefined and empty-string values
      if (!minWidth)
      {
        minWidth = 0;
      }
      else if (minWidth === '*')
      {
        minWidth = +a[i++];
      }
      else if (minWidth.charAt(0) === '*')
      {
        minWidth = +a[minWidth.slice(1, -1)];
      }
      else
      {
        minWidth = +minWidth;
      }

      // Note: undocumented perl feature:
      if (minWidth < 0)
      {
        minWidth = -minWidth;
        leftJustify = true;
      }

      if (!isFinite(minWidth))
      {
        throw new Error('sprintf: (minimum-)width must be finite');
      }

      if (!precision)
      {
        precision = 'fFeE'.indexOf(type) > -1 ? 6 : (type === 'd') ? 0 : undefined;
      }
      else if (precision === '*')
      {
        precision = +a[i++];
      }
      else if (precision.charAt(0) === '*')
      {
        precision = +a[precision.slice(1, -1)];
      }
      else
      {
        precision = +precision;
      }

      // grab value using valueIndex if required?
      value = valueIndex ? a[valueIndex.slice(0, -1)] : a[i++];

      switch (type)
      {
        case 's':
          return formatString(String(value), leftJustify, minWidth, precision, zeroPad, customPadChar);
        case 'c':
          return formatString(String.fromCharCode(+value), leftJustify, minWidth, precision, zeroPad);
        case 'b':
          return formatBaseX(value, 2, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'o':
          return formatBaseX(value, 8, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'x':
          return formatBaseX(value, 16, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'X':
          return formatBaseX(value, 16, prefixBaseX, leftJustify, minWidth, precision, zeroPad).toUpperCase();
        case 'u':
          return formatBaseX(value, 10, prefixBaseX, leftJustify, minWidth, precision, zeroPad);
        case 'i':
        case 'd':
          number = +value || 0;
          number = Math.round(number - number % 1); // Plain Math.round doesn't just truncate
          prefix = number < 0 ? '-' : positivePrefix;
          value = prefix + pad(String(Math.abs(number)), precision, '0', false);
          return justify(value, prefix, leftJustify, minWidth, zeroPad);
        case 'e':
        case 'E':
        case 'f': // Should handle locales (as per setlocale)
        case 'F':
        case 'g':
        case 'G':
          number = +value;
          prefix = number < 0 ? '-' : positivePrefix;
          method = ['toExponential', 'toFixed', 'toPrecision']['efg'.indexOf(type.toLowerCase())];
          textTransform = ['toString', 'toUpperCase'][('eEfFgG'.indexOf(type)) % 2];
          value = prefix + Math.abs(number)[method](precision);
          return justify(value, prefix, leftJustify, minWidth, zeroPad)[textTransform]();
        default:
          return substring;
      }
    }

    return format.replace(regex, doFormat);
  };
  
  Cango.prototype.drawAxes = function(xMin, xMax, yMin, yMax, opts={})
  {
    const axes = new Axes(xMin, xMax, yMin, yMax, opts);
    this.render(axes);
  };

  Cango.prototype.drawBoxAxes = function(xMin, xMax, yMin, yMax, opts)
  {
    const boxAxes = new BoxAxes(xMin, xMax, yMin, yMax, opts);
    this.render(boxAxes);
  };

}()); 
