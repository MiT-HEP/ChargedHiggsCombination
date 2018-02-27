

.PHONY: all
all: .feynhiggs

.feynhiggs: 
	# download feynhiggs
	wget $(shell cat download/feynhiggs.txt | head -n 1)
	#untar
	tar -xzf $(shell cat download/feynhiggs.txt | head -n 1 | sed 's:.*/::g')
	rm $(shell cat download/feynhiggs.txt | head -n 1 | sed 's:.*/::g')
	# compile FeynHiggs
	cd $(shell cat download/feynhiggs.txt | head -n 1 | sed 's:.*/::g' | sed 's:.tar.gz::g') && ./configure && $(MAKE) && make install
	## make aware make that this is done
	touch .feynhiggs

.PHONY: clean
clean:
	-rm .feynhiggs
	-rm -rf $(shell cat download/feynhiggs.txt | head -n 1 | sed 's:.*/::g' | sed 's:.tar.gz::g')
