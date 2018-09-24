clear all;
close all;

totalImagens = dir('*.bmp');
numeroImagens = length(totalImagens); 

for i=1:numeroImagens
   imgEncontrada = totalImagens(i).name;
   img = imread(imgEncontrada);

FaceDetect = vision.CascadeObjectDetector; 
FaceDetect.MergeThreshold = 7 ; 
  fprintf('okok\n')


BB = step(FaceDetect, img) 


for i = 1 : size(BB, 1) 
    
 J = imcrop(img, BB(i, :)); 
 imwrite(J, ['new_', imgEncontrada]);

 %imshow(J);
 
 %pause
 
end
end