'use client';

import { useEffect, useRef } from 'react';

interface QuizQuestion {
  q: string;
  options: string[];
  a: number; // index of correct answer
}

interface QuizData {
  questions: QuizQuestion[];
}

export default function Quiz() {
  const quizContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!quizContainerRef.current) return;
    
    // Find all quiz divs within the container
    const quizDivs = quizContainerRef.current.querySelectorAll('.quiz');
    
    // Process each quiz div
    quizDivs.forEach(div => {
      const dataQuiz = div.getAttribute('data-quiz');
      if (dataQuiz) {
        try {
          const quizData: QuizData = JSON.parse(dataQuiz);
          div.innerHTML = renderQuiz(quizData);
          
          // Add event listeners for answer selection
          div.querySelectorAll('.quiz-option').forEach((option, index) => {
            option.addEventListener('click', () => {
              // Find which question this option belongs to
              const questionIndex = Math.floor(index / quizData.questions[0].options.length);
              const correctAnswer = quizData.questions[questionIndex].a;
              
              // Remove previous selections for this question
              const startIndex = questionIndex * quizData.questions[0].options.length;
              for (let i = 0; i < quizData.questions[0].options.length; i++) {
                const opt = div.querySelector(`.quiz-option[data-index="${startIndex + i}"]`) as HTMLElement;
                if (opt) {
                  opt.classList.remove('selected', 'correct', 'incorrect');
                }
              }
              
              // Mark selected option
              option.classList.add('selected');
              
              // Check if correct
              if (index % quizData.questions[0].options.length === correctAnswer) {
                option.classList.add('correct');
              } else {
                option.classList.add('incorrect');
                // Show correct answer
                const correctOpt = div.querySelector(`.quiz-option[data-index="${startIndex + correctAnswer}"]`) as HTMLElement;
                if (correctOpt) {
                  correctOpt.classList.add('correct');
                }
              }
            });
          });
        } catch (e) {
          console.error('Failed to parse quiz data:', e);
          div.innerHTML = '<p class="text-red-500">Error loading quiz</p>';
        }
      }
    });
  }, []);

  function renderQuiz(data: QuizData): string {
    return data.questions.map((q, qIndex) => {
      const optionsHtml = q.options.map((opt, optIndex) => {
        const globalIndex = qIndex * q.options.length + optIndex;
        return `
          <label class="quiz-option block mb-2 p-3 border rounded cursor-pointer hover:bg-[var(--bg-elev)]/50 transition-colors" 
                 data-index="${globalIndex}">
            <span class="flex items-center space-x-3">
              <span class="w-4 h-4 flex-shrink-0">
                <span class="${optIndex === qIndex * q.options.length + q.a ? 'hidden' : 'block'} w-full h-full bg-[var(--accent-2)]/20"></span>
                <span class="${optIndex === qIndex * q.options.length + q.a ? 'block' : 'hidden'} w-4 h-4 border-2 border-[var(--accent-2)] rounded-full"></span>
              </span>
              ${opt}
            </span>
          </label>
        `;
      }).join('');
      
      return `
        <div class="mb-6">
          <p class="font-medium mb-2">${q.q}</p>
          <div class="space-y-1">${optionsHtml}</div>
        </div>
      `;
    }).join('');
  }

  return (
    <div ref={quizContainerRef} className="mt-8 pt-4 border-t border-[var(--card-border)]/50">
      {/* Quiz components will be injected here by the effect */}
    </div>
  );
}