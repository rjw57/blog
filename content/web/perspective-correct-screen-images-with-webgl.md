Title: Perspective correct phone screen images with WebGL
slug: perspective_correct_screen_images_with_webgl
Date: 2013-08-26
status: draft

<center>![A screenshot of the final product](|filename|/images/screen-images-webgl/leader.png)</center>

*In this post: fake is better than real; a brave new graphical world; projective transformations; CORS issues; bending
WebGL to your will.*

I was recently tagged in a [Google+ post](https://plus.google.com/108243663090085262773/posts/hwPw8oEKBbb) asking for
help on using Web technologies to generate slick images of mobile apps overlaid onto pictures of real devices. The idea
being that shiny pictures make people buy things. In that post I developed a little hack which abused the HTML5 canvas
element to do perspective-correct image warping. In this post I'm going to show you how to do it 'properly'. That is
without having to sacrifice correctness. In order to do this we're going to use WebGL but we're not doing 3D graphics.
This post is all about emulating the 'perspective' tool in Photoshop and is all about 2D graphics.

Without any further ado, here is a JSFiddle which encapsulates the techniques in this post. We'll be talking about all
the checkboxes later on but, for the moment, play with moving the red dots around and checking/un-checking the boxes to
see the effect. The JSFiddle requires WebGL and if your browser doesn't support WebGL, I've included a screenshot at the
start of this post. (Anisotropic filtering is a feature which only some browsers support. If your browser doesn't
support it, the checkbox is disabled but the rest of the demo should work.)

<iframe width="100%" height="650" src="http://jsfiddle.net/rjw57/A6Pgy/embedded/result,js,html,css/" allowfullscreen="allowfullscreen"
frameborder="0"></iframe>

## A first attempt: using the HTML5 canvas API

Let's begin by considering a single point in the input image, $(x, y$), which ends up at $(X, Y)$ on the screen. If
you've played with the 2D canvas, you'll be familiar with it's
[transform method](http://www.w3schools.com/tags/canvas_transform.asp). This method takes six parameters which we'll
call, for the moment, $a$, $b$, $d$, $e$, $g$ and $h$ and sets up a co-ordinate transform on the canvas. Points drawn at
$(x, y)$ will end up at pixel co-ordinate $(X, Y)$ according to the following relation:

$$
\begin{bmatrix}
X \\\\ Y \\\\ 1
\end{bmatrix}
=
\begin{bmatrix}
a & d & g \\\\
b & e & h \\\\
0 & 0 & 1
\end{bmatrix}
\begin{bmatrix}
x \\\\ y \\\\ 1
\end{bmatrix}.
$$

To put it another way:

$$
X = ax + dy + g, \quad \text{and,} \quad Y = bx + ey + h.
$$

This transform will be applied to all points, including those in images draw via the
[drawImage method](http://www.w3schools.com/tags/canvas_drawimage.asp). Given three image points, $(x_1, y_1), \cdots, (x_3, y_3)$,
the *source* points, and corresponding points in the output image, the *destination* points, we can stack all three
equations together into a single matrix equation:

$$
\underbrace{\begin{bmatrix}
X_1 & X_2 & X_3 \\\\ Y_1 & Y_2 & Y_3 \\\\ 1 & 1 & 1
\end{bmatrix}}\_{D}
=
\underbrace{\begin{bmatrix}
a & d & g \\\\
b & e & h \\\\
0 & 0 & 1
\end{bmatrix}}\_{T}
\underbrace{\begin{bmatrix}
x_1 & x_2 & x_3 \\\\ y_1 & y_2 & y_3 \\\\ 1 & 1 & 1
\end{bmatrix}}\_{S}
$$

where we have stacked all the destination points into a single matrix, $D$, and all the source points into a single
matrix, $S$. Assuming $S$ is full-rank, we can recover the parameters we need to feed into the canvas' transform method
by inverting $S$:

$$
T = DS^{-1}.
$$

We can implement this in Javascript using [Numeric.js](http://www.numericjs.com/):

```javascript
function transformationFromTriangleCorners(before, after)
{
    // Return the parameters needed by the transform() 
    // canvas function which will transform the three points in *before* to the
    // corresponding ones in *after*. The points should be specified as
    // [{x:x1,y:y1}, {x:x2,y:y2}, {x:x3,y:y2}].

    var D, S, T;

    // Make S matrix
    S = [
        [ before[0].x, before[1].x, before[2].x ],
        [ before[0].y, before[1].y, before[2].y ],
        [ 1, 1, 1 ]
    ];

    // Make D matrix
    D = [
        [ after[0].x, after[1].x, after[2].x ],
        [ after[0].y, after[1].y, after[2].y ],
        [ 1, 1, 1 ]
    ];

    // Compute T matrix using Numeric. If you wanted, you could work out the
    // inverse of X long-hand but life is too short.
    T = numeric.dot(D, numeric.inv(S));

    // We only want specific elements from T
    return [T[0][0], T[1][0], T[0][1], T[1][1], T[0][2], T[1][2]];
}
```

Notice that we have only needed *three* corresponding points in the source and destination images. (We can only invert a
matrix if it is a square one.) The JSFiddle below shows the result of using this method and the canvas API's transform
method. This uses no WebGL, just the basic 2D canvas support that all modern browsers should have.

<iframe width="100%" height="650" src="http://jsfiddle.net/rjw57/unmR6/embedded/result,js,html,css" allowfullscreen="allowfullscreen"
frameborder="0"></iframe>

The heart of the JSFiddle above is a ``redrawImg()`` function which uses the HTML5 canvas API to draw the screen image:

```javascript
function redrawImg() {
    // imgElement is a <img> element containing the screen image.
    var w = imgElement.naturalWidth, h = imgElement.naturalHeight;

    // The global variable controlPoints specifies the positions in the
    // output image of the screen corners. This variable specifies the
    // corners in screen image co-ordinates:
    var srcPoints = [
        { x: 0, y: 0 },    // top-left
        { x: w, y: 0 },    // top-right
        { x: w, y: h }     // bottom-right
    ];
    
    // Use the three correspondences to compute the transform parameters.
    var T = transformationFromTriangleCorners(srcPoints, controlPoints);
    
    // Get a canvas context and clear any previous image.
    var ctx = canvasElement.getContext('2d');
    ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);
    
    // Draw the transformed image.
    ctx.save();
    ctx.transform(T[0], T[1], T[2], T[3], T[4], T[5]);
    ctx.drawImage(imgElement, 0, 0);
    ctx.restore();
}
```

Unfortunately this suffers from some problems. The first problem is that three points are not enough; we can't get the
screen image to fall exactly on the background phone's screen. Whether the second problem exists for you may depend on
your browser. On my machine the screen image looks 'jagged' and of poor quality compared to the results one can get from
Photoshop. This is particularly noticeable around the small lettering at the bottom of the screen and on fine horizontal
lines. Here's a zoomed in screenshot to show what I mean:

<center>![Using 2D Canvas APIs can lead to artefacts](|filename|/images/screen-images-webgl/affine.png)</center>

A 2D transform like this which is specified by six parameters is called an
[affine transformation](http://en.wikipedia.org/wiki/Affine_transformation). If you play with the example above you
should be able to convince yourself that an affine transformation can represent scaling, rotation, shearing and the
[phantom zone](https://www.youtube.com/watch?v=2u3eQc_rx54#t=65s) but not a
the perspective-like transformation we want. We're going to need a more general transform.

## Projective transforms

If you look back up the page to our matrix equation relating $(x, y)$ and $(X, Y)$ you might notice that the bottom row
of the transform matrix was fixed to be $[0, 0, 1]$. It needs to be that so that the last '1' of $[X, Y, 1]$ on the
left matches the last '1' of $[x, y, 1]$ on the right. To put it another way, the only way to make $1 = cx + fy + 1$
true for all $x$ and $y$ is for $c = f = 0$.

What if we don't force this last row to have that value? What if the first two elements could change? (We'll talk about
the third one later.) This means the last element of the left hand side would no longer be 1. Let's call it $W$:

$$
\begin{bmatrix}
XW \\\\ YW \\\\ W
\end{bmatrix}
=
\begin{bmatrix}
a & d & g \\\\
b & e & h \\\\
c & f & 1
\end{bmatrix}
\begin{bmatrix}
x \\\\ y \\\\ 1
\end{bmatrix}
$$

We've changed from $[X, Y, 1]$ to $[XW, YW, W]$ here so that we can always get back to our original $[X, Y, 1]$ by
dividing by $W$:

$$
\begin{bmatrix}
X \\\\ Y \\\\ 1
\end{bmatrix}
= \frac{1}{W}
\begin{bmatrix}
XW \\\\ YW \\\\ W
\end{bmatrix}.
$$

This explains why it doesn't matter if we set the last element of our transform matrix to 1. Let's try setting it to
some value, $\alpha$, by multiplying the whole transform matrix:

$$
\begin{bmatrix}
\alpha XW \\\\ \alpha YW \\\\ \alpha W
\end{bmatrix}
=
\begin{bmatrix}
\alpha a & \alpha d & \alpha g \\\\
\alpha b & \alpha e & \alpha h \\\\
\alpha c & \alpha f & \alpha
\end{bmatrix}
\begin{bmatrix}
x \\\\ y \\\\ 1
\end{bmatrix}.
$$

No matter what we set $\alpha$ to, as long as it isn't zero, the effect cancels out when we compute $X$ and $Y$ by
dividing by $\alpha W$. Since it doesn't matter what $\alpha$ is, we set it to 1 to make things neater.

We have a more general transform matrix now but how do we work out what the values of $a$ to $h$ actually are given some
source and destination points? Firstly, we note that we have an explicit relation for $W$:

$$
W = cx + fy + 1.
$$

We can multiply that out to give a relation for $X$ and $Y$:

$$
\begin{align}
XW = cxX + fyX + X &= ax + dy + g \\\\
YW = cxY + fyY + Y &= bx + ey + h.
\end{align}
$$

We can re-arrange these to give two equations of similar form:

$$
\begin{align}
xa + 0b - xXc + yd + 0e - yXf + 1g + 0h &= X \\\\
0a + xb - xYc + 0d + ye - yYf + 0g + 1h &= Y,
\end{align}
$$

or in matrix form:

$$
\begin{bmatrix}
x & 0 & -xX & y & 0 & -yX & 1 & 0 \\\\
0 & x & -xY & 0 & y & -yY & 0 & 1
\end{bmatrix}
\begin{bmatrix}
a\\\\b\\\\c\\\\d\\\\e\\\\f\\\\g\\\\h
\end{bmatrix}
=
\begin{bmatrix}
X\\\\Y
\end{bmatrix}.
$$

If we consider four source points $(x_1, y_1), \cdots, (x_4, y_4)$ which map to corresponding destination points $(X_1,
Y_1), \cdots, (X_4, Y_4)$ then we can stack all four pairs of equations together into a single matrix equation:

$$
\underbrace{\begin{bmatrix}
x_1 & 0 & -x_1X_1 & y_1 & 0 & -y_1X_1 & 1 & 0 \\\\
0 & x_1 & -x_1Y_1 & 0 & y_1 & -y_1Y_1 & 0 & 1 \\\\
x_2 & 0 & -x_2X_2 & y_2 & 0 & -y_2X_2 & 1 & 0 \\\\
0 & x_2 & -x_2Y_2 & 0 & y_2 & -y_2Y_2 & 0 & 1 \\\\
x_3 & 0 & -x_3X_3 & y_3 & 0 & -y_3X_3 & 1 & 0 \\\\
0 & x_3 & -x_3Y_3 & 0 & y_3 & -y_3Y_3 & 0 & 1 \\\\
x_4 & 0 & -x_4X_4 & y_4 & 0 & -y_4X_4 & 1 & 0 \\\\
0 & x_4 & -x_4Y_4 & 0 & y_4 & -y_4Y_4 & 0 & 1 \\\\
\end{bmatrix}}\_{A}
\underbrace{\begin{bmatrix}
a\\\\b\\\\c\\\\d\\\\e\\\\f\\\\g\\\\h
\end{bmatrix}}\_{\vec{v}}
=
\underbrace{\begin{bmatrix}
X_1\\\\Y_1\\\\
X_2\\\\Y_2\\\\
X_3\\\\Y_3\\\\
X_4\\\\Y_4
\end{bmatrix}}\_{\vec{u}}.
$$

Stacking everything together like this leads to $A$ being $8 \times 8$ and, since it is square and we assume it to be
full rank, we can solve the matrix equation to get our vector of transform parameters, $\vec{v}$, simply by inverting
$A$:

$$
\vec{v} = A^{-1} \vec{u}.
$$

In Javascript, using the [Numeric.js](http://www.numericjs.com/) library, this looks like the following:

```javascript
function transformationFromQuadCorners(before, after)
{
    // Return the 8 elements of the transformation matrix which maps the points
    // in *before* to corresponding ones in *after*. The points should be
    // specified as [{x:x1,y:y1}, {x:x2,y:y2}, {x:x3,y:y2}, {x:x4,y:y4}].
    // 
    // Note: There are 8 elements because the bottom-right element is assumed to
    // be '1'.
 
    // Form the column vector of 'after' points.
    var u = numeric.transpose([[
        after[0].x, after[0].y, after[1].x, after[1].y,
        after[2].x, after[2].y, after[3].x, after[3].y ]]);
    
    // Form the magic matrix of 'after' and 'before' points.
    var A = [];
    for(var i=0; i<before.length; i++) {
        A.push([
            before[i].x, 0, -after[i].x*before[i].x,
            before[i].y, 0, -after[i].x*before[i].y, 1, 0]);
        A.push([
            0, before[i].x, -after[i].y*before[i].x,
            0, before[i].y, -after[i].y*before[i].y, 0, 1]);
    }
    
    // Solve for v and return the elements as a single array
    return numeric.transpose(numeric.dot(numeric.inv(A), u))[0];
}
```

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
