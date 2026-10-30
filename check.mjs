import assert from 'node:assert/strict';
import {groupWords,parseSubtitles,toSrt} from './web/core.js';
const words=[{text:' Hello',timestamp:[0,.5]},{text:' world.',timestamp:[.5,1]},{text:' Next!',timestamp:[1.3,null]}];
const g=groupWords(words,2);assert.equal(g.length,2);assert.equal(g[1].end,2);assert.equal(g[0].words.length,2);
const srt=toSrt(g),round=parseSubtitles(srt);assert.equal(round.length,2);assert.equal(round[1].end,2);assert.equal(round[0].text,'Hello world.');
assert.equal(parseSubtitles('WEBVTT\n\n00:01.000 --> 00:02.000 align:start\n<b>Hello</b>')[0].text,'Hello');
assert.equal(parseSubtitles('1\n00:00:03,000 --> 00:00:01,000\ninvalid').length,0);
assert.equal(groupWords([],0).length,0);
console.log('Passed: sentence grouping, missing end timestamp, SRT round-trip, VTT cues, invalid cues.');

