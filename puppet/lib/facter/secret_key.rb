# secret_key.rb
Facter.add('secret_key') do
   setcode '/bin/cat /opt/scos-sensor/.secret_key'
end
