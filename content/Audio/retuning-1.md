Title: Retuning Songs With Python and NumPy &mdash; Part 1: Pitch-shifting
Slug: retuning-songs-part-1
status: draft
Date: 2013-07-03
Tags: audio, fft, nump, Python, Friday project

<iframe src="http://player.vimeo.com/video/57685359" width="500" height="375" frameborder="0" webkitAllowFullScreen mozallowfullscreen allowFullScreen></iframe> 

A few months ago a [retuned version] [lmr] of REM's *Losing My Religion* did
the rounds on the Internet. The original song was in the key of A Minor and the
retuned version was in the key of A Major. Depending on your personal view this
either livened up the original or ruined it. In this two-part series I'm going
to show you how you too can make a retuned version of a pop sing using Python
and NumPy. In this part we'll concentrate on pitch-shifting and in the next
part we'll look at how selective pitch-shifting can be used to change the key a
song is performed in.

[lmr]: http://vimeo.com/57685359

## The basics: a tone

A pure tone in an audio signal is a [sinusoid] which is a function giving the
*amplitude* of the signal as a function of the *time*. Digital signals are
usually *sampled*. That is to say that at regular intervals, the value of the
signal is recorded. Each record is termed a *sample*. Audio signals are usually
sampled at 44,100 or 48,000 times per second. We call the number of samples per
second the *sampling rate* and measure it in [Hertz]. The time between samples
is called the *sample period*. If the sample rate is 44,100Hz then the sample
period is 1s/44,100 $\approx$ 22&mu;s.

[sinusoid]: http://en.wikipedia.org/wiki/Sinusoid
[Hertz]: http://en.wikipedia.org/wiki/Hertz

Mathematically, the equation which gives the amplitude of the $t$-th sample, $x_t$ is:

$$ x_t = \cos( \phi + \omega t ).$$

The value $\phi$ is called the *phase* and I'll call $\omega$ the frequence
although for slightly annoying historical reasons, it is actually $2\pi$ times
the frequency as specified in cycles per sample period. Halving $\omega$ halves
the number of cycles per unit time:

![The effect of changing omega](|filename|/images/retuning/sinusoid-1.png)

The effect of changing $\phi$ is a little more subtle: it shifts the signal
left and right. When $\phi = 2\pi$ then the signal is shifted an entire cycle
to the left. If $\phi = 2\pi / 4$ or $\pi = 2\pi / 2$ then the signal is
shifted to the left by one quarter or one half of a cycle respectively:

![The effect of changing phi](|filename|/images/retuning/sinusoid-2.png)

Phase is important because we'll be splitting our entire song up into little
sections in which the sound barely changes. These small sections are called
*frames*. Suppose I want to slow a song by a factor of two. I could do this by
splitting the song into little frames, say 0.02 seconds each, and then
repeating every frame. So instead of reconstructing the signal as frame 1
followed by frame 2 then frames 3, 4 and 5 I reconstruct it as two copies of
frame 1, then two of frame 2 and so on. This will double the length of the song
without changing the pitch. The downside is that the frames do not necessarily
join up.

Let's consider a frame of 512 samples. If I put one with a starting time of
$t_0 = 0$ and another with $t_0 = 512$ then I get something like the following:

![Joining two frames poorly](|filename|/images/retuning/sinusoid-3.png)

Instead I need to shift the *phase* of the second frame so that it joins up
with the first. Assuming I know this *phase-shift*, then I can just change the
value of $\phi$ for the second frame:

![Joining two frames correctly](|filename|/images/retuning/sinusoid-4.png)

