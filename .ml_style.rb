# markdownlint style
# https://github.com/markdownlint/markdownlint/blob/master/docs/creating_styles.md
# Enable all rules by default
all

rule 'MD013', :line_length => 88, :code_blocks => false
rule 'MD007', :indent => 3
rule 'MD024', :allow_different_nesting => true
