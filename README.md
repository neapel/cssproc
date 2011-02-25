This python (2 or 3) CSS preprocessor has only one feature: unwrap nested blocks.

It doesn't care about the content of the rule blocks as long as braces are balanced. Other python CSS processors have the habit of being too specific for my taste. This one only messes up your whitespace.

	#page {
		a {
			{ text-decoration: none }
			> span { meh }
			:hover, :focus { color: blue }
		}
		*:hover { bar }
	}
	a, b { :hover { baz } }

Becomes

	:::CSS
	#page a { text-decoration: none }
	#page a > span { meh }
	#page a:hover, #page a:focus { color: blue }
	#page *:hover { bar } /* equivalent to: #page :hover */
	a:hover, b:hover { baz }

Nested selectors are concatenated with spaces, except for pseudoclasses and -elements. Use `*:` to prevent that.

The script acts as a filter when called directly: `python cssproc.py < in.css > out.css` or like a make-rule: `python file1.cssp file2.cssp` creates/overwrites file1.css and file2.css. If the input file's extension is css, output is to stdout, if it's something else, output is to corresponding .css (will overwrite existing files)
