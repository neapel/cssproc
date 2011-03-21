#!/usr/bin/env python

import re

class Stash(object):
	''' stores arbitrary objects in a string '''

	def __init__(self, token = '<' * 10):
		self.stashed_r = r'(?P<stashed>%s(?P<id>\d*)%s)' % (re.escape(token), re.escape(token))
		self.rpat = token + '%s' + token
		self.stashed = re.compile(self.stashed_r)

		self.stuff = dict()
		self.count = 0

	def pop(self, i):
		x = self.stuff[i]
		del self.stuff[i]
		return x

	def push(self, x):
		self.count = self.count + 1
		i = '%d' % self.count
		self.stuff[i] = x
		return self.rpat % i

	def pop_all(self, s):
		for m in self.stashed.finditer(s):
			yield self.pop(m.group('id'))

	def has(self, s):
		return self.stashed.search(s) != None

	def resolve(self, s, f):
		return self.stashed.sub(
			lambda match: f(self.pop(match.group('id'))),
			s)


def combine(outer, inner):
	''' combine two nested selectors '''

	if ',' in inner:
		return ', '.join([combine(outer, rule.strip()) for rule in inner.split(',')])
	if ',' in outer:
		return ', '.join([combine(rule.strip(), inner) for rule in outer.split(',')])

	if inner and not re.match('^(\.|\:)', inner):
		inner = ' ' + inner
	return outer + inner


def sub(code):
	''' expand nested CSS rules in the given string '''

	from itertools import count

	stash = Stash()
	rec = re.compile(r'''
		(?P<start> \s*)
		(?P<stripped>
			(?P<st> %s)
		|
			(?P<comment> /\* [\s\S]*? \*/)
		|
			(?P<atstm> @[^{}]*?(;|$) )
		|
			(?P<atblk>
				(?P<atsel> @[^;{}]*?)
				{
					(?P<atcnt> [^{}]* )
				}
			)
		|
			(?P<blk>
				(?P<sel> [^{}]*?)
				{
					(?P<cnt> [^{}]* )
				}
			)
		)
		(?P<end> \s*)
	''' % stash.stashed_r, re.VERBOSE)


	def pretty(stuff):
		sel, cnt = stuff
		cnt = '\n'.join([ '\t' + l.strip() for l in cnt.strip().splitlines() ])
		return '\n%s {\n%s\n}\n' % (sel, cnt)


	# Do 2 passes per level over the code
	for step in count():
		found = [False]

		def replace_inner(match):
			text = match.group(0)
			if match.group('blk'):
				# get selector and rules
				sel = match.group('sel').strip()
				cnt = match.group('cnt')
				s = match.group('stripped')

				# inner blocks are stashed: process.
				if stash.has(s):
					found[0] = True
					return ''.join([
						stash.push((
							combine(sel, inner_sel),
							inner_cnt
						))
						for inner_sel, inner_cnt in stash.pop_all(s)
					])

				else:
					# nothing to process inside.
					return stash.push((sel, cnt))

			elif match.group('atblk'):
				# unstash inner blocks
				sel = match.group('atsel').strip()
				cnt = stash.resolve(match.group('atcnt'), pretty)
				return stash.push((sel, cnt))
			else:
				# pass through rest
				return match.group(0)

		code = rec.sub(replace_inner, code)
		if step > 1 and not found[0]:
			break

	return stash.resolve(code, pretty)




if __name__ == '__main__':
	import sys
	if len(sys.argv) == 1:
		# filter mode
		sys.stderr.write('filter mode\n')
		sys.stderr.flush()
		sys.stdout.write(sub(''.join(sys.stdin)))

	else:
		# extension replacement mode: name.ext -> name.css
		import os

		for name in sys.argv[1:]:
			inf = open(name, 'r')
			base, ext = os.path.splitext(name)
			if ext.lower() != 'css':
				out = base + os.path.extsep + 'css'
				outf = open(out, 'w')
				sys.stderr.write('%s -> %s\n' % (name, out))
			else:
				outf = sys.stdout
				sys.stderr.write('%s -> stdout\n' % name)
			sys.stderr.flush()
			outf.write(sub(''.join(inf)))
