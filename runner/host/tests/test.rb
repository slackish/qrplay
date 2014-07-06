#!/usr/bin/env ruby

#stdout/stderr test
$stdout.puts "Hello world to 1"
$stderr.puts "Hello world to 2"

lines=STDIN.read.split("\n")
puts lines

#file write test
File.open("/tmp/testing", 'w') { |file| file.write("zomg\n") }
