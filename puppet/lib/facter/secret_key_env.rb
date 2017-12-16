# secret_key_env.rb
Facter.add('secret_key_env') do
   setcode 'echo $SECRET_KEY'
end
