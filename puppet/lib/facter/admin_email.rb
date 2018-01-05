# admin_email.rb
Facter.add('admin_email') do
   setcode '/bin/cat /opt/scos-sensor/.admin_email'
end
