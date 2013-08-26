Title: Perspective correct phone screen images with WebGL
slug: perspective_correct_screen_images_with_webgl
Date: 2013-08-26
status: draft

sggdsds
sdgsd
ffdds

```javascript

// The control points which represent the top-left, top-right and bottom
// right of the image. These will be wires, via d3.js, to the handles
// in the svg element.
var controlPoints = [
    { x: 100, y: 100 },
    { x: 300, y: 100 },
    { x: 100, y: 400 },
    { x: 300, y: 400 }
];

// UI for controlling quality
var anisotropicFilteringElement = document.getElementById('anisotropicFiltering');
var mipMappingFilteringElement = document.getElementById('mipMapping');
var linearFilteringElement = document.getElementById('linearFiltering');

// Options for controlling quality.
var qualityOptions = { };
syncQualityOptions();

// UI for saving image
document.getElementById('saveResult').onclick = saveResult;

// Reflect any changes in quality options
anisotropicFilteringElement.onchange = syncQualityOptions;
mipMappingFilteringElement.onchange = syncQualityOptions;
linearFilteringElement.onchange = syncQualityOptions;

// Wire in the control handles to dragging. Call 'redrawImg' when they change.
var controlHandlesElement = document.getElementById('controlHandles');
setupControlHandles(controlHandlesElement, redrawImg);

// Wire up the control handle toggle
var drawControlPointsElement = document.getElementById('drawControlPoints');
drawControlPointsElement.onchange = function() {
    controlHandlesElement.style.visibility =
        !!(drawControlPointsElement.checked) ? 'visible' : 'hidden';
}

// Create a WegGL context from the canvas which will have the screen image
// rendered to it. NB: preserveDrawingBuffer is needed for rendering the
// image for download. (Otherwise, the canvas appears to have nothing in
// it.)
var screenCanvasElement = document.getElementById('screenCanvas');
var glOpts = { antialias: true, depth: false, preserveDrawingBuffer: true };
var gl =
    screenCanvasElement.getContext('webgl', glOpts) ||
    screenCanvasElement.getContext('experimental-webgl', glOpts);
if(!gl) {
    addError("Your browser doesn't seem to support WebGL.");
}

// See if we have the anisotropic filtering extension by trying to get
// if from the WebGL implementation.
var anisoExt =
    gl.getExtension('EXT_texture_filter_anisotropic') ||
    gl.getExtension('MOZ_EXT_texture_filter_anisotropic') ||
    gl.getExtension('WEBKIT_EXT_texture_filter_anisotropic');

// If we failed, tell the user that their image will look like poo on a
// stick.
if(!anisoExt) {
    anisotropicFilteringElement.checked = false;
    anisotropicFilteringElement.disabled = true;
    addError("Your browser doesn't support anisotropic filtering. "+
             "Ordinary MIP mapping will be used.");
}

// Setup the GL context compiling the shader programs and returning the
// attribute and uniform locations.
var glResources = setupGlContext();

// This object will store the width and height of the screen image in
// normalised texture co-ordinates in its 'w' and 'h' fields.
var screenTextureSize;

// The only readon this element exists in the DOM is too (potentially)
// cache the image for us before this script is run and to specity
// the screen image URL in a more obvious place.
var imgElement = document.getElementById('screen');
imgElement.style.display = 'none';

// Create an element to hold the screen image and arracnge for loadScreenTexture
// to be called when the image is loaded.
var screenImgElement = new Image();
screenImgElement.crossOrigin = '';
screenImgElement.onload = loadScreenTexture;
screenImgElement.src = imgElement.src;

function setupGlContext() {
    // Store return values here
    var rv = {};
    
    // Vertex shader:
    var vertShaderSource = [
        'attribute vec2 aVertCoord;',
        'uniform mat4 uTransformMatrix;',
        'varying vec2 vTextureCoord;',
        'void main(void) {',
        '    vTextureCoord = aVertCoord;',
        '    gl_Position = uTransformMatrix * vec4(aVertCoord, 0.0, 1.0);',
        '}'
    ].join('\n');

    var vertexShader = gl.createShader(gl.VERTEX_SHADER);
    gl.shaderSource(vertexShader, vertShaderSource);
    gl.compileShader(vertexShader);

    if (!gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS)) {
        addError('Failed to compile vertex shader:' +
              gl.getShaderInfoLog(vertexShader));
    }
       
    // Fragment shader:
    var fragShaderSource = [
        'precision mediump float;',
        'varying vec2 vTextureCoord;',
        'uniform sampler2D uSampler;',
        'void main(void)  {',
        '    gl_FragColor = texture2D(uSampler, vTextureCoord);',
        '}'
    ].join('\n');

    var fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
    gl.shaderSource(fragmentShader, fragShaderSource);
    gl.compileShader(fragmentShader);

    if (!gl.getShaderParameter(fragmentShader, gl.COMPILE_STATUS)) {
        addError('Failed to compile fragment shader:' +
              gl.getShaderInfoLog(fragmentShader));
    }
    
    // Compile the program
    rv.shaderProgram = gl.createProgram();
    gl.attachShader(rv.shaderProgram, vertexShader);
    gl.attachShader(rv.shaderProgram, fragmentShader);
    gl.linkProgram(rv.shaderProgram);

    if (!gl.getProgramParameter(rv.shaderProgram, gl.LINK_STATUS)) {
        addError('Shader linking failed.');
    }
        
    // Create a buffer to hold the vertices
    rv.vertexBuffer = gl.createBuffer();

    // Find and set up the uniforms and attributes        
    gl.useProgram(rv.shaderProgram);
    rv.vertAttrib = gl.getAttribLocation(rv.shaderProgram, 'aVertCoord');
    gl.enableVertexAttribArray(rv.vertAttrib);
        
    rv.transMatUniform = gl.getUniformLocation(rv.shaderProgram, 'uTransformMatrix');
    rv.samplerUniform = gl.getUniformLocation(rv.shaderProgram, 'uSampler');
        
    // Create a texture to use for the screen image
    rv.screenTexture = gl.createTexture();
    
    return rv;
}

function loadScreenTexture() {
    if(!gl || !glResources) { return; }
    
    var image = screenImgElement;
    var extent = { w: image.naturalWidth, h: image.naturalHeight };
    
    gl.bindTexture(gl.TEXTURE_2D, glResources.screenTexture);
    
    // Scale up the texture to the next highest power of two dimensions.
    var canvas = document.createElement("canvas");
    canvas.width = nextHighestPowerOfTwo(extent.w);
    canvas.height = nextHighestPowerOfTwo(extent.h);
    
    var ctx = canvas.getContext("2d");
    ctx.drawImage(image, 0, 0, image.width, image.height);
    
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas);
    
    if(qualityOptions.linearFiltering) {
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER,
                         qualityOptions.mipMapping
                             ? gl.LINEAR_MIPMAP_LINEAR
                             : gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    } else {
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, 
                         qualityOptions.mipMapping
                             ? gl.NEAREST_MIPMAP_NEAREST
                             : gl.LINEAR);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    }
    
    if(anisoExt) {
        // turn the anisotropy knob all the way to 11 (or down to 1 if it is
        // switched off).
        var maxAniso = qualityOptions.anisotropicFiltering ?
            gl.getParameter(anisoExt.MAX_TEXTURE_MAX_ANISOTROPY_EXT) : 1;
        gl.texParameterf(gl.TEXTURE_2D, anisoExt.TEXTURE_MAX_ANISOTROPY_EXT, maxAniso);
    }
    
    if(qualityOptions.mipMapping) {
        gl.generateMipmap(gl.TEXTURE_2D);
    }
    
    gl.bindTexture(gl.TEXTURE_2D, null);
    
    // Record normalised height and width.
    screenTextureSize = {
        w: extent.w / canvas.width,
        h: extent.h / canvas.height
    };
    
    // Redraw the image
    redrawImg();
}

function isPowerOfTwo(x) { return (x & (x - 1)) == 0; }
 
function nextHighestPowerOfTwo(x) {
    --x;
    for (var i = 1; i < 32; i <<= 1) {
        x = x | x >> i;
    }
    return x + 1;
}

function redrawImg() {
    //var drawSkeleton = !!(drawSkeletonElement.checked);
    //svgElement.style.visibility = drawSkeleton ? 'visible' : 'hidden';

    if(!gl || !glResources || !screenTextureSize) { return; }
    
    var w = screenTextureSize.w, h = screenTextureSize.h;
    var vpW = screenCanvasElement.width;
    var vpH = screenCanvasElement.height;

    var srcPoints = [
        { x: 0, y: 0 }, // top-left
        { x: w, y: 0 }, // top-right
        { x: 0, y: h }, // bottom-left
        { x: w, y: h }  // bottom-right
    ];
    
    // Find where the control points are in 'window coordinates'. I.e.
    // where thecanvas covers [-1,1] x [-1,1]. Note that we have to flip
    // the y-coord.
    var dstPoints = [];
    for(var i=0; i<controlPoints.length; i++) {
        dstPoints.push({
            x: (2 * controlPoints[i].x / vpW) - 1,
            y: -(2 * controlPoints[i].y / vpH) + 1
        });
    }
    
    // Get the transform
    var T = transformationFromQuadCorners(srcPoints, dstPoints);
    
    // set background to full transparency
    gl.clearColor(0,0,0,0);
    gl.viewport(0, 0, vpW, vpH);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    
    // setup the vertex buffer with the source points
    var vertices = [];
    for(var i=0; i<srcPoints.length; i++) {
        vertices.push(srcPoints[i].x);
        vertices.push(srcPoints[i].y);
    }
        
    gl.bindBuffer(gl.ARRAY_BUFFER, glResources.vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.DYNAMIC_DRAW);
    
    gl.useProgram(glResources.shaderProgram);

    // draw the triangles
    gl.vertexAttribPointer(glResources.vertAttrib, 2, gl.FLOAT, false, 0, 0);
    gl.uniformMatrix4fv(
        glResources.transMatUniform,
        false, [
            // This is 'T' unravelled in column-major order.
            T[0][0], T[1][0], T[2][0], T[3][0],
            T[0][1], T[1][1], T[2][1], T[3][1],
            T[0][2], T[1][2], T[2][2], T[3][2],
            T[0][3], T[1][3], T[2][3], T[3][3]
        ]);
        
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, glResources.screenTexture);
    gl.uniform1i(glResources.samplerUniform, 0);

    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);    
}

function transformationFromQuadCorners(before, after)
{
    /*
     Return the 16 element transformation matrix which transforms
     the points in *before* to corresponding ones in *after*.
     The points should be specified as
     [{x:x1,y:y1}, {x:x2,y:y2}, {x:x3,y:y2}, {x:x4,y:y4}].
    */
    
    /* See http://alumni.media.mit.edu/~cwren/interpolator/ */

    var b = numeric.transpose([[
        after[0].x, after[0].y,
        after[1].x, after[1].y,
        after[2].x, after[2].y,
        after[3].x, after[3].y ]]);
    
    var A = [];
    for(var i=0; i<before.length; i++) {
        A.push([
            before[i].x, before[i].y, 1, 0, 0, 0,
            -after[i].x*before[i].x, -after[i].x*before[i].y ]);
        A.push([
            0, 0, 0, before[i].x, before[i].y, 1,
            -after[i].y*before[i].x, -after[i].y*before[i].y ]);
    }
       
    var v = numeric.transpose(numeric.dot(numeric.inv(A), b))[0];
    
    var T = [
        [v[0], v[1],   0, v[2]],
        [v[3], v[4],   0, v[5]],
        [   0,    0,   1,    0],
        [v[6], v[7],   0,    1]
    ];
    
    return T;
}

function syncQualityOptions() {
    qualityOptions.anisotropicFiltering = !!(anisotropicFilteringElement.checked);
    qualityOptions.mipMapping = !!(mipMappingFilteringElement.checked);
    qualityOptions.linearFiltering = !!(linearFilteringElement.checked);
    
    // re-load the texture if possible
    loadScreenTexture();
}

function setupControlHandles(controlHandlesElement, onChangeCallback)
{
    // Use d3.js to provide user-draggable control points
    var rectDragBehav = d3.behavior.drag()
        .on('drag', function(d,i) {
                d.x += d3.event.dx; d.y += d3.event.dy;
                d3.select(this).attr('cx',d.x).attr('cy',d.y);
                onChangeCallback();
            });
    
    var dragT = d3.select(controlHandlesElement).selectAll('circle')
            .data(controlPoints)
        .enter().append('circle')
            .attr('cx', function(d) { return d.x; })
            .attr('cy', function(d) { return d.y; })
            .attr('r', 30)
            .attr('class', 'control-point')
            .call(rectDragBehav);
}

function addError(message)
{
    var container = document.getElementById('errors');
    var errMessage = document.createElement('div');
    errMessage.textContent = message;
    errMessage.className = 'errorMessage';
    container.appendChild(errMessage);
}

function saveResult() {
    var resultCanvas = document.createElement('canvas');
    resultCanvas.width = screenCanvasElement.width;
    resultCanvas.height = screenCanvasElement.height;
    var ctx = resultCanvas.getContext('2d');
       
    var bgImage = new Image();
    bgImage.crossOrigin = '';
    bgImage.onload = function() {
        ctx.drawImage(bgImage, 0, 0);
        ctx.drawImage(screenCanvasElement, 0, 0);
        Canvas2Image.saveAsPNG(resultCanvas);
    }
    bgImage.src = document.getElementById('background').src;
}
```

```css
#container {
    position: relative;
    width: 500px; height: 507px;
}

#container * {
    position: absolute;
}

.errorMessage {
    border: 1px solid #dFb5b4;
    background: #fcf2f2;
    color: #c7254e;
    padding: 0.5em;
    border-radius: 5px;
}

circle.control-point {
    fill: red;
    fill-opacity: 0.25;
}

circle.control-point:hover {
    stroke: yellow;
    stroke-width: 2px;
}
```

```html
<div id="errors">
    <!-- Any errors will go here wrapped in a div with an 'errorMessage' class. -->
</div>
<p>
    Drag points around to distort image.
    <input type="checkbox" checked="1" id="drawControlPoints"></input>
    <label for="drawControlPoints">Draw control points.</label>
    <input type="checkbox" checked="1" id="anisotropicFiltering"></input>
    <label for="anisotropicFiltering">Anisotropic filtering.</label>
    <input type="checkbox" checked="1" id="mipMapping"></input>
    <label for="mipMapping">MIP mapping.</label>
    <input type="checkbox" checked="1" id="linearFiltering"></input>
    <label for="linearFiltering">(Bi-/Tri-)linear filtering.</label>
    <button id="saveResult">Download as PNG</button>
</p>
<div id="container">
    <!-- If background and/or screen image are not hosted on the
         same domain as this page, the host must support CORS. -->
    <img id="background" src="http://i.imgur.com/eFSch02.jpg">
    <img id="screen" src="http://i.imgur.com/vsZypFu.png">
    <canvas width="500" height="507" id="screenCanvas"></canvas>
    <svg width="500" height="507" id="controlHandles"></svg>
</div>
```
