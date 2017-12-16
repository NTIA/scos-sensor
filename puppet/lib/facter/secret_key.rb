# secret_key.rb
Facter.add('secret_key') do
   setcode '/bin/cat /opt/scos/.secret_key'
end
