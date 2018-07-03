# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw, ImageFont
import os

class FontException(Exception): pass

class DescriptionFile(object):
        
    def __init__(self, title, casting, productionYear, description, posterFile, rating, outputFile):
        
        self.maxTextWidth = 1900
        self.title = title
        self.casting = casting[:300]
        self.productionYear = productionYear
        self.description = description
        self.posterFile = posterFile
        self.rating = rating
        self.outputFile = outputFile
        
    def buildMovieDescriptionFile(self):
        """
        Creates the description file given a poster and the description
        """
        posterAreaSize = 800., 1000.
        
        # creates the enclosing image
        image = Image.new('RGB', (1920, 1080), (180, 180, 180))
        
        if self.posterFile is not None and os.path.isfile(self.posterFile) and os.path.getsize(self.posterFile) > 0:
            
            try:
                poster = Image.open(self.posterFile)
            
                posterWidth, posterHeight = poster.size
                ar = posterWidth / float(posterHeight)
                
                if ar > posterAreaSize[0] / posterAreaSize[1]:
                    posterHeight = int(posterAreaSize[0] / ar)
                    posterWidth = int(posterAreaSize[0])
                else:
                    posterWidth = int(ar * posterAreaSize[1])
                    posterHeight = int(posterAreaSize[1]) 
                
                poster2 = poster.resize((posterWidth, posterHeight), Image.ANTIALIAS)
            
                image.paste(poster2, (40, 40))
            
            except:
                pass
            
        # creates draw for description
        draw = ImageDraw.Draw(image)
        draw.line((960, 20, 960, 1060), fill=(0, 0, 0), width=4)
        
        writeBottom = self.writeText(self.title, draw, 980, 20, 40, 'center', style="bold")
        self.writeText('Année de production: ', draw, 980, writeBottom + 60, 24, style="italic")
        writeBottom = self.writeText(str(self.productionYear), draw, 1300, writeBottom + 60, 24, style="normal")
        self.writeText('Note: ', draw, 980, writeBottom, 24, style="italic")
        writeBottom = self.writeText('%.1f/5' % self.rating, draw, 1300, writeBottom, 24, style="normal")
        self.writeText('Acteurs: ', draw, 980, writeBottom, 24, style="italic")
        writeBottom = self.writeText(self.casting, draw, 1300, writeBottom, 24, style="normal")
        
        self.writeText(self.description, draw, 980, writeBottom + 80, 24)
        image.save(self.outputFile, 'JPEG')
        
    def writeText(self, text, draw, positionX, positionY, fontSize, aligned='left', style='normal'):
        """
        Writes the text on the image referenced by draw argument
        Method breaks line when max width is reached
        
        Returns the bottom position of the written text
        """
        if text is None:
            text = ""
        
        veraFontFolder = '/usr/share/fonts/truetype/ttf-bitstream-vera/'
        
        # add text
        if style == 'bold':
            font = ImageFont.truetype(veraFontFolder + "VeraBd.ttf", fontSize)
        elif style == 'normal':
            font = ImageFont.truetype(veraFontFolder + "Vera.ttf", fontSize)
        elif style == 'italic':
            font = ImageFont.truetype(veraFontFolder + "VeraIt.ttf", fontSize)
        elif style == 'bold/italic':
            font = ImageFont.truetype(veraFontFolder + "VeraBI.ttf", fontSize)
        else:
            raise FontException("style %s not recognized" % style)
        
        currentLine = ''
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            for word in paragraph.split(' '):
                textWidth, textHeight = draw.textsize(currentLine + ' ' + word, font)
                if textWidth + positionX < self.maxTextWidth:
                    currentLine += ' ' + word
                else:
                    if aligned == 'left':
                        draw.text((positionX, positionY + 5), currentLine, fill=0, font=font)
                    elif aligned == 'center':
                        draw.text(((self.maxTextWidth - draw.textsize(currentLine, font)[0]) / 2 + positionX / 2, positionY + 5), currentLine, fill=0, font=font)
                    currentLine = word
                    positionY += 5 + textHeight 
                    
        if aligned == 'left':
            draw.text((positionX, positionY + 5), currentLine, fill=0, font=font)
        elif aligned == 'center':
            draw.text(((self.maxTextWidth - draw.textsize(currentLine, font)[0]) / 2 + positionX / 2, positionY + 5), currentLine, fill=0, font=font)
        
        return positionY + draw.textsize(currentLine, font)[1] + 5
        
    @staticmethod
    def createThumbnail(picture, thumbnailFile):
        """
        Create a thumbnail from picture
        """
        if not os.path.isfile(picture):
            return ""
        
        try:
            image = Image.open(picture)
            image.thumbnail((128, 128), Image.ANTIALIAS)
            image.save(thumbnailFile, "JPEG")
            
            return thumbnailFile
        except:
            return ""

        
if __name__ == '__main__':
    
    df = DescriptionFile('Rock machin truc toto titi flkjsqmdljfqm sdfldskjglhj sdglkjljsdfg', 'Jude Law, Rachel Weisz, Joseph Fiennes, Bob Hoskins, Ed Harris', '2020', 'RGB functions, given as "rgb(red, green, blue)" where the colour values are integers in the range 0 to 255. Alternatively, the color values can be given as three percentages (0% to 100%). For example, "rgb(255,0,0)" and "rgb(100%,0%,0%)" both specify pure red.', 
                         '/home/worm/.pydlnadms/data/18369270.jpg', 
                         3.5, 
                         '/home/worm/.pydlnadms/data/18369270.descr.jpg')
    df.buildMovieDescriptionFile()
#    DescriptionFile.createThumbnail('/home/worm/.pydlnadms/data/18369270.jpg', '/home/worm/.pydlnadms/data/18369270-thumb.jpg')
        