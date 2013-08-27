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

This transform will be applied to all points, including those in images drawn via the
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
    // inverse of S long-hand but life is too short.
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

Stacking everything together like this leads to $A$ being square and, if we assume it to be full rank, we can solve the
matrix equation to get our vector of transform parameters, $\vec{v}$, simply by inverting $A$:

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

## A second attempt: CSS

OK, you can relax now. The heavy maths is over for the moment and we can move back into the pragmatic world of web
programming. We've got a Javascript function which, given four points in the source and destination images, will give us
the magic eight numbers we need to slot into the transform matrix to get us there. Unfortunately the canvas' transform
method only takes *six* parameters; it's not general enough for our needs.

Luckily the nice people over at Apple decided that web pages needed more bling and so they implemented a CSS
[transform property](https://developer.mozilla.org/en-US/docs/Web/CSS/transform-function) which is working its way
through the standardisation process and is already present, albeit vendor-prefixed, in most modern browsers. Instead of
drawing our image with the canvas API, we could set the transform property directly on an ``<img>`` element via CSS:

```css
img#screen {
    /* Scale the image by 1/2 and offset it by (-100, -50). */
    transform: matrix(0.5, 0, 0, 0.5, -100, -50);
}
```

Surprise, surprise, the six parameters to the *matrix* CSS transform function match those of the canvas transform
method. As we noted above, these six parameters aren't quite enough for us. Luckily there is a *matrix3d* function which
takes a whopping 16 values. Surely there's enough room there to slot in our eight values? The 16 values are entries in
the following transformation matrix which, as before, takes our source image co-ordinates and maps them to the
destination co-ordinates using the 16 values $\\{ t_1, \cdots, t_{16} \\}$ in the following way:

$$
\begin{bmatrix}
XW \\\\ YW \\\\ ZW \\\\ W
\end{bmatrix}
=
\begin{bmatrix}
t_1 & t_5 & t_9 & t_{13} \\\\
t_2 & t_6 & t_{10} & t_{14} \\\\
t_3 & t_7 & t_{11} & t_{15} \\\\
t_4 & t_8 & t_{12} & t_{16}
\end{bmatrix}
\begin{bmatrix}
x \\\\ y \\\\ z \\\\ 1
\end{bmatrix}.
$$

What are these $z$ and $Z$ numbers? Aren't web pages fundamentally 2D affairs? Yes and no. Although they are certainly
laid out in 2D, each element in a web page has a notional 'depth' or
[z-index](http://www.w3schools.com/cssref/pr_pos_z-index.asp). Those elements with a greater $z$ index appear 'above'
elements with a smaller one. It is this $z$ value which is fed into the transform above. Although we're doing a
perspective-like transform *we are only warping the image in 2D*. We do *not* want to rotate the image in 3D. Remember
that we are only trying to emulate the perspective warp feature in Photoshop. We're not writing a 3D engine. So we
don't really care what the final $Z$ value actually is. We can set most of the elements of the matrix by comparing our
2D transform to the matrix equation and using '0' to ignore the $z$ co-ordinate:

$$
\begin{bmatrix}
XW \\\\ YW \\\\ ZW \\\\ W
\end{bmatrix}
=
\begin{bmatrix}
a & d & 0 & g \\\\
b & e & 0 & h \\\\
t_3 & t_7 & t_{11} & t_{15} \\\\
c & f & 0 & 1
\end{bmatrix}
\begin{bmatrix}
x \\\\ y \\\\ z \\\\ 1
\end{bmatrix}.
$$

This leaves only one row of the matrix to set: the row which determines $ZW$. Since we don't really care what the depth
of our output is, we'll just leave it alone:

$$
\begin{bmatrix}
XW \\\\ YW \\\\ ZW \\\\ W
\end{bmatrix}
=
\begin{bmatrix}
a & d & 0 & g \\\\
b & e & 0 & h \\\\
0 & 0 & 1 & 01 \\\\
c & f & 0 & 1
\end{bmatrix}
\begin{bmatrix}
x \\\\ y \\\\ z \\\\ 1
\end{bmatrix}.
$$

We could've set it to any other value we chose, but leaving it alone is prudent. Now that we know how to work
out what parameters to pass to the *matrix3d* function, writing the ``drawImg()`` function is straightforward:

```javascript
function redrawImg() {
    var w = imgElement.naturalWidth, h = imgElement.naturalHeight;

    var srcPoints = [
        { x: 0, y: 0 },    // top-left
        { x: w, y: 0 },    // top-right
        { x: w, y: h },    // bottom-right
        { x: 0, y: h }     // bottom-left
    ];
    
    // Use the four correspondences to compute the transform parameters.
    var v = transformationFromQuadCorners(srcPoints, controlPoints);
    
    // Construct a matrix3d() call slotting in the transform parameters.
    var trans = 'matrix3d(' +
        v[0] + ',' + v[1] + ',0.0,' + v[2] + ',' +
        v[3] + ',' + v[4] + ',0.0,' + v[5] + ',' +
        '0.0, 0.0, 0.0, 0.0,' +
        v[6] + ',' + v[7] + ',0.0, 1.0)';
 
    // Set the <img> element's CSS transform property or the vendor-prefixed equivalent.
    imgElement.style.webkitTransform = trans;
    imgElement.style.MozTransform = trans;
    imgElement.style.msTransform = trans;
    imgElement.style.OTransform = trans;
    imgElement.style.transform = trans;
}
```

A final little wrinkle is that we need to use the
[transform-origin CSS property](http://www.w3schools.com/cssref/css3_pr_transform-origin.asp) on the ``<img>`` to make
sure that $(0,0)$ really *is* the top-left corner.  The result is below. **Note:** for some reason, you may need to
wiggle a control point before the CSS change takes effect. Any suggestions as to why are most welcome.

<iframe width="100%" height="650" src="http://jsfiddle.net/rjw57/kbQPW/embedded/result,js,html,css" allowfullscreen="allowfullscreen"
frameborder="0"></iframe>

And the result is not at all bad. (Although, on Firefox, it is very jittery.) If your browser is highly GPU-accelerated
the edges of the screen image will even be anti-aliased. Using CSS is not an ideal solution since a) one of the design
goals was to have a 'Save as PNG' button but trying to screenshot the browser via Javascript is nigh-on impossible, and
b) there are still some jaggies in the actual screen image itself. The jaggies are particularly noticeable on the blue
lines in this zoomed in image:

<center>![Using CSS gets us most of the way there](|filename|/images/screen-images-webgl/css-perspective.png)</center>

We've gone as far as the browser can insulate us from the dark world of GPUs. It's time to move to&hellip; WebGL.

## A brave new world: WebGL

At some level WebGL is just another canvas API. Instead of getting a ``'2d'`` context from the canvas and using that for
all drawing operations, one gets a ``'webgl'`` context:

```javascript
// Create a WegGL context from the canvas which will have the screen image
// rendered to it. NB: preserveDrawingBuffer is needed for rendering the
// image for download. (Otherwise, the canvas appears to have nothing in
// it.)
var screenCanvasElement = document.getElementById('screenCanvas');
var glOpts = { antialias: true, depth: false, preserveDrawingBuffer: true };
var gl = screenCanvasElement.getContext('webgl', glOpts) ||
         screenCanvasElement.getContext('experimental-webgl', glOpts);
if(!gl) {
    addError("Your browser doesn't seem to support WebGL.");
}
```

(I've assumed the existence of a function, ``addError()``, which will report an error to the user in a slightly prettier
way than using ``alert()``.)

The only wrinkle is that, depending on your browser, WebGL may or may not be marked as experimental. We have to try
both and see what comes out. The ``antialias`` and ``depth`` options are hints to the browser. In our application we
want the output to be as smooth as possible and we won't be needing a depth buffer since we're not doing any 3D stuff.
As noted in the comment the ``preserveDrawingBuffer`` is needed to support the 'Save as PNG' functionality.

### Vertex and fragment shaders

Unlike the 2D canvas version where we do most of the work in the ``redrawImg()`` function, we do most of the work in the
WebGL world in the initial setup of the context. This is intentional; WebGL wants to make the per-frame draw call as
much like 'do it again but over here' as possible. As in the canvas example we draw something at $(x, y)$ in WebGL and
this results in something happening at pixel $(X, Y)$. The WebGL pipeline looks like this:

* We send WebGL a set of points, or *vertices*, which we are going to use to draw the image.
* WebGL runs each vertex through a little program called a *vertex shader* to convert the points into canvas pixel
  co-ordinates. The vertex shader may also attach a little bit of data to each output vertex. This is termed a *varying*
  value
* WebGL fills in triangles between each vertex. For each pixel in the triangle, WebGL calls another little program to
  determine the pixel's colour. In WebGL a pixel is called a *fragment* and hence this program is called the *fragment
  shader*. The fragment shader can also read the varying value but that value is interpolated based on the pixel's
  position within the triangle.

Varying values perhaps need more explanation. There is an
[example](http://www.opengl.org/sdk/docs/tutorials/ClockworkCoders/varying.php) in the OpenGL SDK which illustrates
their effect. In this example, in the vertex shader, each vertex outputs a different colour, red, green or blue, as a
varying. The fragment shader then just uses the colour it gets as its output. As you can see, the varying values get
interpolated between vertices:

<center>![Varying values in GLSL](|filename|/images/screen-images-webgl/varying.gif)</center>

We're going to abuse the pipeline to draw our screen image. We're going to send the source co-ordinates to WebGL and use
the vertex shader to do the matrix multiply for us. We'll record the original source co-ordinate as a varying value
which will then be picked up by the fragment shader. This value will be used as a co-ordinate to get the right pixel
value from the screen image.

All of that takes longer to explain in English than it does in code. Here's the source for our vertex shader:

```glsl
// The source co-ordinate.
attribute vec2 aVertCoord;

// The transformation matrix.
uniform mat4 uTransformMatrix;

// A varying value holding the original source co-ordinate.
varying vec2 vTextureCoord;

void main(void) {
    // Record the original source co-ordinate for the fragment shader.
    vTextureCoord = aVertCoord;

    // Work out the position in canvas co-ordinates of this vertex.
    gl_Position = uTransformMatrix * vec4(aVertCoord, 0.0, 1.0);
}
```

And here is the code for the fragment shader:

```glsl
// A hint to WebGL that we only need medium accuracy in the result; we're
// not doing weather simulation here!
precision mediump float;

// The varying value from the vertex shader.
varying vec2 vTextureCoord;

// A sampler lets us get pixel values from an image.
uniform sampler2D uSampler;

void main(void)  {
    // The output colour is the value of the screen image at vTextureCoord.
    gl_FragColor = texture2D(uSampler, vTextureCoord);
}
```

If you count up all the non-comment, non-variable declaration, lines there are three lines in total that do something:

1. remember the original source co-ordinate;
2. work out the destination co-ordinate by multiplying by the transform matrix; and
3. get the fragment's colour from the screen image.

In our WebGL context setup we need to a) compile these shaders and b) link them together into a single *shader program*.
A shader program contains the vertex and fragment shaders used to create a particular effect. We can switch between
shader programs within one draw call to get different effects although in our application we only need one shader
program. Compiling and linking the shaders into one program is easy, if tedious:

```javascript
// These variables are set to the source to our shaders.
var vertShaderSource, fragShaderSource;

// Create the vertex shader and compile it.
var vertexShader = gl.createShader(gl.VERTEX_SHADER);
gl.shaderSource(vertexShader, vertShaderSource);
gl.compileShader(vertexShader);

// Check for errors compiling the vertex shader.
if (!gl.getShaderParameter(vertexShader, gl.COMPILE_STATUS)) {
    addError('Failed to compile vertex shader:' +
             gl.getShaderInfoLog(vertexShader));
}

// Create the fragment shader and compile it.
var fragmentShader = gl.createShader(gl.FRAGMENT_SHADER);
gl.shaderSource(fragmentShader, fragShaderSource);
gl.compileShader(fragmentShader);

// Check for errors compiling the fragment shader.
if (!gl.getShaderParameter(fragmentShader, gl.COMPILE_STATUS)) {
    addError('Failed to compile fragment shader:' +
             gl.getShaderInfoLog(fragmentShader));
}

// 'Link' the shaders into a single program.
var shaderProgram = gl.createProgram();
gl.attachShader(shaderProgram, vertexShader);
gl.attachShader(shaderProgram, fragmentShader);
gl.linkProgram(shaderProgram);

// Check for any errors linking the program.
if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
    addError('Shader linking failed.');
}
```

There are three 'inputs' to the shaders; an *attribute* which is the vertex position itself and two *uniforms* giving
the transform matrix and the screen image. An *attribute* is something which changes with each vertex and a *uniform* is
something which stays the same in one frame.

When we come to actually draw the screen in ``redrawImg()`` we will need to set these inputs. WebGL provides a way to
get the 'location' of these attributes for later use:

```javascript
// Make our shader program the current program in use.
gl.useProgram(shaderProgram);

// Find the uniforms and attributes        
var vertAttrib = gl.getAttribLocation(shaderProgram, 'aVertCoord');
var transMatUniform = gl.getUniformLocation(shaderProgram, 'uTransformMatrix');
var samplerUniform = gl.getUniformLocation(shaderProgram, 'uSampler');
```
### Vertex buffers

The 2D canvas API is, in WebGL-speak, an immediate mode API. That is to say that when we say 'create this path' we do so
by giving it the points. WebGL is more indirect than that. In WebGL we set up a 'buffer' object to hold the co-ordinates
of the points and then say to WebGL 'draw some triangles joining up the points in that buffer'. The idea behind this
being that if you are re-drawing a complex model every frame you don't want to be specifying the co-ordinates of all the
vertices of that model each and every frame. You want to say just once 'hey, WebGL, here's the data for a bad guy' and
then each frame you can say 'draw a bad guy using the data I gave you'. For our application this isn't very helpful but
we must work within the world we're given.

Complex though that might sound, actually doing it is fairly simple. We need to create, once, a vertex buffer to hold
the source co-ordinates of the quadrilateral, or *quad*, we want to draw and add the vertices to it. The ``srcPoints``
array hold the *x*- and *y*-co-ordinates of a quadrilateral which covers the screen. We'll cover what those co-ordinates
actually are later.

```javascript
// Create a buffer to hold the vertices
var vertexBuffer = gl.createBuffer();

// Fill the vertex buffer with the source points
var vertices = [];
for(var i=0; i<srcPoints.length; i++) {
    vertices.push(srcPoints[i].x);
    vertices.push(srcPoints[i].y);
}
    
gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);a
gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STATIC_DRAW);
```

The ``gl.bindBuffer()`` dance is typical of WebGL APIs. One manipulates an object, in this case ``vertexBuffer``, by
'binding' it to a *target*, in this case ``gl.ARRAY_BUFFER``, and then performing operations on that target as in the
call to ``gl.bufferData``. This sort of 'indirect' object-orientation is a hang over from the C-focused days of OpenGL.
The ``gl.STATIC_DRAW`` is a hint to WebGL that we'll be drawing using these co-ordinates often but updating them rarely.
In fact, in our application, we never touch them again.

### The screen image texture

In WebGL an image whose pixel values can be queried is called a *texture*. Creating a texture is done once in the
initial setup and is a single call:

```javascript
var screenTexture = gl.createTexture();
```

Setting up that texture to contain the right pixels is a bit annoying. The main annoyance is that WebGL really, really
wants your textures to have widths and heights which are powers of 2. That is your textures should be 1, 2, 4, 8, 16,
&hellip; wide and tall. If your screen image satisfies that then great. Unfortunately not many real-world images do. We
wire up the following ``loadScreenTexture()`` function to the screen image element via the ``onload`` event. This
function's aim is to a) copy the image to a canvas element whose width and height are a power of two, b) initialise the
``screenTexture`` with the image's content and c) initialise the srcPoints array.

Let's cover parts a) and b) first:

```javascript
function loadScreenTexture() {
    // This is the <img> element whose src attribute is the screen image.
    var image = screenImgElement;

    // Extract the width and height of the image.
    var extent = { w: image.naturalWidth, h: image.naturalHeight };
        
    // Bind the screen texture to the current 2D texture target.
    gl.bindTexture(gl.TEXTURE_2D, screenTexture);
    
    // Scale up the texture to the next highest power of two dimensions.
    var canvas = document.createElement("canvas");
    canvas.width = nextHighestPowerOfTwo(extent.w);
    canvas.height = nextHighestPowerOfTwo(extent.h);
    
    var ctx = canvas.getContext("2d");
    ctx.drawImage(image, 0, 0, image.width, image.height);
    
    // Copy the image from the canvas into the texture.
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, canvas);

    // Specify that when we use the texture2d() function in the fragment shader,
    // we want to use the pixel whose co-ordinate is the nearest for the asked for
    // co-ordinate.
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);

    // Initialise srcPoints (discussed below)
    // ...
}
```

Again we see the 'bind' idiom used; the screen texture is bound to the ``gl.TEXTURE_2D`` target and that target is
modified via WebGL calls. The ``gl.texImage2D`` call is where the texture actually gets it's content and the
``gl.texParameteri`` calls specify how co-ordinates passed to the ``texture2d()`` get turned into pixel values. In the
case above we specify that we look for the nearest pixel and use that value.

Part c) is a little more involved. The ``texture2d()`` function takes what are called 'normalised' texture co-ordinates.
These are co-ordinates where the top-left of the image has co-ordinate (0,0) and the bottom-right has co-ordinate (1,1)
*irrespective of the number of pixels in the texture*. What this means is that we have to do a little bit of arithmetic
to work out how much of the texture our image covers in the second half of ``loadScreenTexture()``:

```javascript
// Record normalised height and width.
var w = extent.w / canvas.width, h = extent.h / canvas.height;

// Initialise the global srcPoints array.
srcPoints = [
    { x: 0, y: 0 }, // top-left
    { x: w, y: 0 }, // top-right
    { x: 0, y: h }, // bottom-left
    { x: w, y: h }  // bottom-right
];
```

Note that one can't initialise the vertex buffer until the ``srcPoints`` array is initialised. I'd recommend looking at
the JSFiddle source to see the exact ordering that I used.

### Drawing the screen

And so we move to the ``redrawImg()`` function itself. We're going to draw the screen as two triangles which share a
common diagonal. WebGL has a drawing primitive called a 'triangle strip' where points are joined up with triangles
according to this diagram from Wikipedia:

<center>![A triangle strip](|filename|/images/screen-images-webgl/Triangle_Strip.png)</center>

Now we see why we had to specify the source points in such a strange order. To draw the quadrilateral ABDC we need to
send the points in the order A, B, C, D; we need to join up the corners to draw an 'N' on the screen.

As a final wrinkle, the final canvas co-ordinates in WebGL are not in pixels. The output from the vertex shader is
assumed to be in normalised 'window co-ordinates'. Instead of the canvas having a top-left at (0, 0) and a bottom right
at (width, height), the WebGL canvas has a *bottom*-left at (-1, -1) and a *top*-right at (1, 1). We need to do a little
fiddling with the ``controlPoints`` to take account of this.

Once we have the vertices into the vertex buffer and the texture all set up, the actual drawing of the 'triangle strip'
is just one call. We can now write the ``redrawImg()`` function:

```javascript
void redrawImg() {
    // Get the width and height of the canvas element we're drawing to. This is the
    // viewport width and viewport height.
    var vpW = screenCanvasElement.width;
    var vpH = screenCanvasElement.height;

    // Find where the control points are in normalised 'window coordinates'. That is
    // a co-ordinate system where the x co-ordinate and y co-ordinate both vary from
    // -1 to 1. Note: we have to flip the y-coord.
    var dstPoints = [];
    for(var i=0; i<controlPoints.length; i++) {
        dstPoints.push({
            x: (2 * controlPoints[i].x / vpW) - 1,
            y: -(2 * controlPoints[i].y / vpH) + 1
        });
    }

    // Set background colour to full transparency and clear the canvas.
    gl.clearColor(0, 0, 0, 0);
    gl.viewport(0, 0, vpW, vpH);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    // Bind our vertex buffer.
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);

    // Specify that we'll use it for our 'aVertCoord' attribute. The vertex
    // buffer is laid out as 2 values per co-ordinate, separated by 0 values
    // starting 0 values from the start of the buffer.
    gl.enableVertexAttribArray(vertAttrib);
    gl.vertexAttribPointer(vertAttrib, 2, gl.FLOAT, false, 0, 0);

    // Set the transformation matrix.
    gl.uniformMatrix4fv(
        transMatUniform,
        false, [
            v[0], v[1],    0, v[2],
            v[3], v[4],    0, v[5],
               0,    0,    0,    0,
            v[6], v[7],    0,    1
        ]);
        
    // Set the screen texture. WebGL can have multiple textures active at once.
    // Here we activate texture '0', set it to the screen texture and then
    // associate the texture sampler uniform with texture '0'.
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, screenTexture);
    gl.uniform1i(samplerUniform, 0);

    // Actually draw the screen. Use the 4 vertices starting 0 vertices from
    // the start of our vertex buffer.
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
```
